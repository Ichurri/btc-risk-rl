"""Synthetic fixtures only: these prices are not historical market evidence."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from conftest import synthetic_rows

from btc_risk_rl.config import STEP_MS, Config, utc_ms
from btc_risk_rl.data.segmentation import build_mask, build_tables
from btc_risk_rl.features.market import FEATURES, TrainScaler


def small_config(config):
    data = config.model_dump(mode="json")
    data["data"].update(
        warmup_start="2023-01-01T00:00:00Z",
        train_start="2023-01-10T00:00:00Z",
        validation_start="2023-06-01T00:00:00Z",
    )
    return Config.model_validate(data)


def fixture_rows(config):
    start, end = utc_ms(config.data.warmup_start), utc_ms(config.data.test_start)
    return synthetic_rows(start, (end - start) // STEP_MS)


def test_policy_mask_preserves_sources_and_records_three_reasons(config):
    c = small_config(config)
    rows = fixture_rows(c)
    early, missing, reopening = rows[100][0], rows[101][0], rows[102][0]
    rows[100][6] -= 12345
    approved = {early: rows[100][6], missing: None}
    del rows[101]
    original = json.dumps(rows)
    frame, mask, quality = build_mask(rows, c, approved)
    assert json.dumps(rows) == original
    assert len(frame) == len(rows)
    assert quality["status"] == "failed"  # strict gate remains unchanged
    indexed = mask.set_index("open_time")
    assert indexed.loc[early, "reason"] == "early_close"
    assert indexed.loc[missing, "reason"] == "missing"
    assert indexed.loc[reopening, "reason"] == "reopening"
    assert not indexed.loc[missing, "present"]
    assert pd.isna(indexed.loc[missing, "close_time"])
    assert set(indexed.loc[[early, missing, reopening], "block_id"]) == {0}
    assert indexed.loc[early - STEP_MS, "segment_id"] == 0
    assert indexed.loc[reopening + STEP_MS, "segment_id"] == 1


@pytest.mark.parametrize("kind", ["new_gap", "late", "bad_price", "conflict", "early_changed"])
def test_unapproved_or_invalid_data_fail_closed(config, kind):
    c = small_config(config)
    rows = fixture_rows(c)
    t = rows[100][0]
    rows[100][6] -= 500
    approved = {t: rows[100][6]}
    if kind == "new_gap":
        del rows[150]
    elif kind == "late":
        rows[150][6] += 1
    elif kind == "bad_price":
        rows[100][4] = "nan"  # even quarantined data must remain structurally valid
    elif kind == "conflict":
        rows.append(rows[100].copy())
        rows[-1][5] = "999"
    else:
        rows[100][6] -= 1
    with pytest.raises(ValueError):
        build_mask(rows, c, approved)


def test_validation_anomaly_is_never_automatically_segmented(config):
    c = small_config(config)
    rows = fixture_rows(c)
    t = utc_ms(c.data.validation_start)
    approved = {t: None}
    rows = [r for r in rows if r[0] != t]
    with pytest.raises(ValueError, match="training"):
        build_mask(rows, c, approved)


def test_features_restart_and_do_not_respond_to_future_or_previous_segment(config):
    c = small_config(config)
    rows = fixture_rows(c)
    rows[300][6] -= 1
    approved = {rows[300][0]: rows[300][6]}
    frame, mask, _ = build_mask(rows, c, approved)
    tables = build_tables(frame, mask, c)
    obs = tables["features.csv"]
    second = obs[obs.segment_id == 1]
    assert second.iloc[0].open_time == rows[302 + 42][0]
    changed = json.loads(json.dumps(rows))
    for r in changed[:300] + changed[700:]:
        for j in range(1, 5):
            r[j] = str(float(r[j]) * 2)
    f2, m2, _ = build_mask(changed, c, approved)
    obs2 = build_tables(f2, m2, c)["features.csv"]
    take = (obs.open_time >= rows[344][0]) & (obs.open_time < rows[700][0])
    np.testing.assert_array_equal(obs.loc[take, FEATURES], obs2.loc[take, FEATURES])


@pytest.mark.parametrize("length,expected", [(222, 0), (223, 1)])
def test_exact_episode_minimum_after_reset(config, length, expected):
    c = small_config(config)
    rows = fixture_rows(c)
    first, last = 100, 102 + length
    rows[first][6] -= 1
    rows[last][6] -= 1
    approved = {rows[i][0]: rows[i][6] for i in (first, last)}
    f, m, _ = build_mask(rows, c, approved)
    tables = build_tables(f, m, c)
    episodes = tables["episodes.csv"]
    assert len(episodes[episodes.segment_id == 1]) == expected
    if expected:
        row = episodes[episodes.segment_id == 1].iloc[0]
        assert row.initial_observation_ms == rows[144][0]
        assert row.first_target_ms == rows[145][0]
        assert row.last_target_ms == rows[last - 1][0]
        assert row.transitions == 180


def test_scaler_eligibility_and_validation_reuse(config, tmp_path):
    c = small_config(config)
    rows = fixture_rows(c)
    f, m, _ = build_mask(rows, c, {})
    tables = build_tables(f, m, c)
    features = tables["features.csv"]
    fit = tables["fit_observations.csv"]
    expected = features[features.partition == "train"].open_time.tolist()
    assert fit.open_time.tolist() == expected
    feature_frame = features.set_index(pd.to_datetime(features.open_time, unit="ms", utc=True))
    scaler = TrainScaler.fit(
        feature_frame[FEATURES],
        pd.Timestamp(c.data.train_start),
        pd.Timestamp(c.data.validation_start),
    )
    path = tmp_path / "scaler.json"
    path.write_text(json.dumps(scaler.to_dict()))
    restored = TrainScaler(**json.loads(path.read_text()))
    before = path.read_bytes()
    val = feature_frame.loc[feature_frame.partition == "validation", FEATURES]
    z = restored.transform(val)
    np.testing.assert_array_equal(z, (val - scaler.mean) / scaler.scale)
    assert path.read_bytes() == before
    assert restored.fit_count == len(expected)
    # Changing validation cannot change the training fitting sample or its parameters.
    for r in rows:
        if r[0] >= utc_ms(c.data.validation_start):
            for j in range(1, 5):
                r[j] = str(float(r[j]) * 10)
    f2, m2, _ = build_mask(rows, c, {})
    changed = build_tables(f2, m2, c)["features.csv"]
    pd.testing.assert_frame_equal(
        features[features.partition == "train"], changed[changed.partition == "train"]
    )


def test_all_episodes_and_transition_boundaries(config):
    c = small_config(config)
    f, m, _ = build_mask(fixture_rows(c), c, {})
    tables = build_tables(f, m, c)
    transitions = tables["transitions.csv"]
    val = transitions[transitions.partition == "validation"]
    assert val.iloc[0].target_ms == utc_ms(c.data.validation_start)
    assert val.iloc[0].observation_ms == utc_ms(c.data.validation_start) - STEP_MS
    assert val.iloc[-1].target_ms == utc_ms(c.data.test_start) - STEP_MS
    episodes = tables["episodes.csv"]
    assert set(episodes.partition) == {"train"}
    assert (episodes.first_target_ms >= utc_ms(c.data.train_start)).all()
    assert (episodes.last_target_ms < utc_ms(c.data.validation_start)).all()
    assert ((episodes.last_target_ms - episodes.first_target_ms) == 179 * STEP_MS).all()


def test_final_boundary_rejected(config):
    c = small_config(config)
    rows = fixture_rows(c)
    rows += synthetic_rows(utc_ms(c.data.test_start), 1)
    with pytest.raises(ValueError, match="outside"):
        build_mask(rows, c, {})


def synthetic_raw_with_approved_anomalies(config, raw, diagnosis):
    """Use approved timestamps with synthetic OHLCV, explicitly marked in manifest."""
    import shutil

    from btc_risk_rl.data.binance import sha256

    inventory_source = Path("docs/evidence/diagnosis/inventory")
    raw.mkdir()
    diagnosis.mkdir()
    shutil.copy2(inventory_source / "inventory.csv", diagnosis / "inventory.csv")
    inventory = pd.read_csv(diagnosis / "inventory.csv")
    missing = set()
    early = {}
    for r in inventory.itertuples():
        t = utc_ms(pd.Timestamp(r.open_utc))
        if r.type == "missing":
            missing.add(t)
        else:
            early[t] = utc_ms(pd.Timestamp(r.close_utc))
    rows = [r for r in fixture_rows(config) if r[0] not in missing]
    for r in rows:
        if r[0] in early:
            r[6] = early[r[0]]
    (raw / "page-0000.json").write_text(json.dumps(rows))
    manifest = dict(
        status="download_complete_not_quality_accepted",
        source="synthetic_test_fixture",
        symbol="BTCUSDT",
        interval="4h",
        start_inclusive_ms=utc_ms(config.data.warmup_start),
        end_exclusive_ms=utc_ms(config.data.test_start),
        final_test_accessed=False,
        pages=[dict(file="page-0000.json", sha256=sha256(raw / "page-0000.json"), rows=len(rows))],
    )
    (raw / "manifest.json").write_text(json.dumps(manifest))
    impact = json.loads((inventory_source / "impact.json").read_text())
    impact["raw_manifest_sha256"] = sha256(raw / "manifest.json")
    (diagnosis / "impact.json").write_text(json.dumps(impact))


def test_pipeline_acceptance_and_readonly_audit(config, tmp_path, monkeypatch):
    from btc_risk_rl.data.segmented_audit import verify_segmented
    from btc_risk_rl.data.segmented_pipeline import prepare_segmented

    raw, diagnosis, out = tmp_path / "raw", tmp_path / "diagnosis", tmp_path / "out"
    synthetic_raw_with_approved_anomalies(config, raw, diagnosis)
    manifest = prepare_segmented(config, raw, out, diagnosis)
    assert manifest["status"] == "accepted"
    report = json.loads((out / "coverage.json").read_text())
    assert report["train"]["usable_transitions"] == 10054
    assert report["train"]["candidate_starts_180"] == 7048
    assert report["train"]["episode_reachable_targets"] == 9733
    assert report["validation"]["usable_transitions"] == 2190
    saved = {p.name: p.read_bytes() for p in out.iterdir()}

    def forbidden(*args, **kwargs):
        raise AssertionError("Audit must reuse persisted parameters, not fit")

    monkeypatch.setattr(TrainScaler, "fit", forbidden)
    assert verify_segmented(config, raw, out, diagnosis)["status"] == "passed"
    assert saved == {p.name: p.read_bytes() for p in out.iterdir()}
    with pytest.raises(FileExistsError):
        prepare_segmented(config, raw, out, diagnosis)


@pytest.mark.parametrize("target", ["episodes.csv", "observations.csv", "scaler.json"])
def test_artifact_tampering_is_rejected_even_if_hash_updated(config, tmp_path, target):
    from btc_risk_rl.data.binance import sha256
    from btc_risk_rl.data.segmented_audit import verify_segmented
    from btc_risk_rl.data.segmented_pipeline import prepare_segmented

    raw, diagnosis, out = tmp_path / "raw", tmp_path / "diagnosis", tmp_path / "out"
    synthetic_raw_with_approved_anomalies(config, raw, diagnosis)
    prepare_segmented(config, raw, out, diagnosis)
    path = out / target
    if target == "scaler.json":
        value = json.loads(path.read_text())
        value["mean"][0] += 1
        path.write_text(json.dumps(value))
    else:
        table = pd.read_csv(path, float_precision="round_trip")
        if target == "episodes.csv":
            table.loc[0, "last_target_ms"] += STEP_MS
        else:
            table.loc[0, "return_1"] += 1
        table.to_csv(path, index=False, float_format="%.17g")
    manifest = json.loads((out / "manifest.json").read_text())
    manifest["files"][target] = sha256(path)
    (out / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        verify_segmented(config, raw, out, diagnosis)


def test_final_manifest_is_blocked_before_reading_pages(config, tmp_path, monkeypatch):
    from btc_risk_rl.data import binance
    from btc_risk_rl.data.segmented_pipeline import prepare_segmented

    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "manifest.json").write_text(
        json.dumps(
            dict(
                start_inclusive_ms=utc_ms(config.data.test_start),
                end_exclusive_ms=utc_ms(config.data.test_end),
                status="download_complete_not_quality_accepted",
                pages=[{"file": "never-read.json"}],
            )
        )
    )

    def forbidden(path):
        raise AssertionError("Must reject reserved range before any page access")

    monkeypatch.setattr(binance, "sha256", forbidden)
    with pytest.raises(ValueError, match="reserved"):
        prepare_segmented(config, raw, tmp_path / "out")
    assert not (tmp_path / "out/manifest.json").exists()


def test_cli_exposes_separate_prepare_and_readonly_verify():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "btc_risk_rl.cli", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "prepare-segmented-development" in result.stdout
    assert "verify-segmented-development" in result.stdout


def test_timestamp_tampering_of_one_millisecond_is_rejected():
    from btc_risk_rl.data.segmented_audit import same_table

    expected = pd.DataFrame({"open_time": [1512086400000]})
    actual = pd.DataFrame({"open_time": [1512086400001]})
    with pytest.raises(ValueError, match="mismatch"):
        same_table(actual, expected, "one millisecond")


def test_fit_includes_short_segments_and_terminal_observations(config):
    c = small_config(config)
    rows = fixture_rows(c)
    for i in (100, 160):
        rows[i][6] -= 1
    approved = {rows[i][0]: rows[i][6] for i in (100, 160)}
    f, m, _ = build_mask(rows, c, approved)
    tables = build_tables(f, m, c)
    short_fit = tables["fit_observations.csv"].query("segment_id == 1")
    assert short_fit.open_time.tolist() == [rows[i][0] for i in range(144, 160)]
    assert not (tables["episodes.csv"].segment_id == 1).any()
    assert rows[159][0] in set(short_fit.open_time)  # terminal, before the next exclusion


def test_failed_auditor_cannot_accept_dataset(config, tmp_path, monkeypatch):
    from btc_risk_rl.data import segmented_audit
    from btc_risk_rl.data.segmented_pipeline import prepare_segmented

    raw, diagnosis, out = tmp_path / "raw", tmp_path / "diagnosis", tmp_path / "out"
    synthetic_raw_with_approved_anomalies(config, raw, diagnosis)

    def reject(*args, **kwargs):
        raise ValueError("Synthetic forced audit rejection")

    monkeypatch.setattr(segmented_audit, "verify_segmented", reject)
    with pytest.raises(ValueError, match="audit rejection"):
        prepare_segmented(config, raw, out, diagnosis)
    assert json.loads((out / "manifest.json").read_text())["status"] == "failed"
    assert (out / "failure.json").exists()
    assert not (out / "audit.json").exists()


@pytest.mark.parametrize("change", ["page", "manifest", "inventory", "reopening", "coverage"])
def test_source_or_diagnostic_changes_block_acceptance(config, tmp_path, change):
    from btc_risk_rl.data.segmented_pipeline import prepare_segmented

    raw, diagnosis, out = tmp_path / "raw", tmp_path / "diagnosis", tmp_path / "out"
    synthetic_raw_with_approved_anomalies(config, raw, diagnosis)
    if change == "page":
        (raw / "page-0000.json").write_text("[]")
    elif change == "manifest":
        value = json.loads((raw / "manifest.json").read_text())
        value["source"] = "changed"
        (raw / "manifest.json").write_text(json.dumps(value))
    elif change == "inventory":
        table = pd.read_csv(diagnosis / "inventory.csv")
        table.loc[0, "close_utc"] = "2018-01-04T02:00:00+00:00"
        table.to_csv(diagnosis / "inventory.csv", index=False)
    else:
        value = json.loads((diagnosis / "impact.json").read_text())
        if change == "reopening":
            value["reopening_candidates"].pop()
        else:
            value["scenarios"]["B_quarantine_plus_reopening"]["train"]["candidate_starts_180"] += 1
        (diagnosis / "impact.json").write_text(json.dumps(value))
    with pytest.raises(ValueError):
        prepare_segmented(config, raw, out, diagnosis)
    assert (out / "failure.json").exists()
    if (out / "manifest.json").exists():
        assert json.loads((out / "manifest.json").read_text())["status"] != "accepted"
