"""One-time, audited H1 training-prefix export. Never runs a learning unit."""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from btc_risk_rl.config import STEP_MS, utc_ms
from btc_risk_rl.data.binance import sha256
from btc_risk_rl.data.config_compatibility import audit_config_compatibility
from btc_risk_rl.env.training_view import prefix

TABLES = {
    "bars.csv": "open_time",
    "observations.csv": "open_time",
    "features.csv": "open_time",
    "episodes.csv": "last_target_ms",
    "transitions.csv": "target_ms",
}
METADATA = ("scaler.json", "audit.json")


def _timestamp(line, index):
    return int(line.split(b",")[index])


def _export_prefix(source, destination, column, lower, end):
    """Copy original row bytes; inspect only the timestamp of the first 2023 row."""
    count, first, last, excluded = 0, None, None, None
    with source.open("rb") as reader, destination.open("xb") as writer:
        header = reader.readline()
        if not header.endswith(b"\n"):
            raise ValueError(f"Invalid H1 CSV header: {source.name}")
        columns = header.decode("utf-8").strip().split(",")
        if column not in columns:
            raise ValueError(f"Missing H1 time column: {source.name}")
        index = columns.index(column)
        writer.write(header)
        for line in reader:
            moment = _timestamp(line, index)
            if moment >= end:
                excluded = moment
                break
            if moment < lower or (last is not None and moment < last):
                raise ValueError(f"Nonchronological/out-of-scope H1 prefix: {source.name}")
            writer.write(line)
            count += 1
            first = moment if first is None else first
            last = moment
        writer.flush()
        os.fsync(writer.fileno())
    if not count:
        raise ValueError(f"Empty H1 training prefix: {source.name}")
    return dict(rows=count, first_included_ms=first, last_included_ms=last,
                first_excluded_ms=excluded, sha256=sha256(destination))


def _audit_prefix(source, destination, column, end, expected_count):
    """Independent byte-by-byte and row-by-row comparison with H1's prefix."""
    with source.open("rb") as original, destination.open("rb") as derived:
        header = original.readline()
        if derived.readline() != header:
            raise ValueError(f"H1 prefix header mismatch: {source.name}")
        index = header.decode("utf-8").strip().split(",").index(column)
        count = 0
        for line in original:
            if _timestamp(line, index) >= end:
                break
            if derived.readline() != line:
                raise ValueError(f"H1 prefix row mismatch: {source.name} row {count + 1}")
            count += 1
        if derived.readline() or count != expected_count:
            raise ValueError(f"H1 prefix length mismatch: {source.name}")
    return count


def _audit_training(config, prepared, shard, parent_sha, manifest_sha):
    """Recompute training-only index, exclusion, segment and scaler checks."""
    from btc_risk_rl.agents.market_source import TrainingMarket

    source = TrainingMarket(config, prepared, expected_manifest=parent_sha,
                            training_shard=shard,
                            expected_shard_manifest=manifest_sha)
    view = source._view
    train_lo, train_hi = utc_ms(config.data.train_start), utc_ms(config.data.validation_start)
    mask = prefix(prepared / "mask.csv", "open_time", train_hi)
    mask = mask.loc[mask.partition == "train"]
    exclusions = {name: int((mask.reason == name).sum())
                  for name in ("missing", "early_close", "reopening")}
    coverage = json.loads((prepared / "coverage.json").read_text())["train"]
    if (exclusions != coverage["exclusions"]
            or len(view._episodes) != coverage["candidate_starts_180"]
            or len(view._transitions) != coverage["usable_transitions"]
            or view._episodes.segment_id.nunique() != coverage["segments_with_180"]
            or view._bars.loc[view._bars.partition == "train", "segment_id"].nunique()
            != coverage["segments"]):
        raise ValueError("Training-only H1 coverage/exclusion mismatch")
    for sid, group in view._bars.groupby("segment_id", sort=True):
        if not (group.index.to_series().diff().dropna() == STEP_MS).all():
            raise ValueError(f"Noncontiguous training shard segment: {sid}")
    paths, usable = 0, set()
    for episode_id in source.route_ids:
        path = view.training_path(episode_id)
        if (path.partition != "train" or len(path.times) != 181
                or path.times[1] < train_lo or path.times[-1] >= train_hi
                or (path.times[1:] - path.times[:-1] != STEP_MS).any()):
            raise ValueError(f"Invalid indexed training path: {episode_id}")
        paths += 1
        usable.add(path.segment_id)
    if paths != 7048 or len(usable) != coverage["segments_with_180"]:
        raise ValueError("Training path coverage mismatch")
    return dict(accepted_starts=len(source.route_ids), validated_paths=paths,
                usable_segments=len(usable), all_train_segments=coverage["segments"],
                exclusions=exclusions, train_transitions=len(view._transitions),
                fit_count=source.audit["fit_count"], normalizer_refitted=False,
                validation_rows_exported=0)


def _write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def audit_training_shard(config, prepared, shard, *, expected_manifest,
                         expected_shard_manifest):
    """Independently recheck the published bytes against accepted H1."""
    prepared, shard = Path(prepared).resolve(), Path(shard).resolve()
    parent_path = prepared / "manifest.json"
    if sha256(parent_path) != expected_manifest:
        raise ValueError("H1 accepted manifest hash mismatch")
    parent = json.loads(parent_path.read_text())
    for name, expected in parent["files"].items():
        if Path(name).name != name or sha256(prepared / name) != expected:
            raise ValueError(f"H1 product hash mismatch: {name}")
    if sha256(shard / "manifest.json") != expected_shard_manifest:
        raise ValueError("training shard manifest hash mismatch")
    manifest = json.loads((shard / "manifest.json").read_text())
    for name, expected in manifest["files"].items():
        if sha256(shard / name) != expected:
            raise ValueError(f"training shard hash mismatch: {name}")
    end = utc_ms(config.data.validation_start)
    rows = {}
    for name, column in TABLES.items():
        with (shard / name).open("rb") as stream:
            expected_rows = sum(1 for _ in stream) - 1
        rows[name] = _audit_prefix(prepared / name, shard / name, column,
                                   end, expected_rows)
    checks = _audit_training(config, prepared, shard, expected_manifest,
                             expected_shard_manifest)
    return dict(status="passed", checked_utc=datetime.now(timezone.utc).isoformat(),
                parent_manifest_sha256=expected_manifest,
                training_shard_manifest_sha256=expected_shard_manifest,
                prefix_equal_row_by_row=True, audited_rows=rows, **checks)


def export_training_shard(config, prepared, output, *, expected_manifest):
    """Publish only after full source-hash, prefix and route audits succeed."""
    prepared, output = Path(prepared).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    if (utc_ms(config.data.train_start), utc_ms(config.data.validation_start)) != (
        1514764800000, 1672531200000
    ):
        raise ValueError("P2R export requires training 2018–2022")
    stage = output.with_name(f"{output.name}.partial-{uuid.uuid4().hex}")
    stage.mkdir(parents=True, exist_ok=False)
    try:
        parent_path = prepared / "manifest.json"
        if sha256(parent_path) != expected_manifest:
            raise ValueError("H1 accepted manifest hash mismatch")
        parent = json.loads(parent_path.read_text())
        if parent.get("status") != "accepted" or parent.get("policy") != "B_ADR_004":
            raise ValueError("H1 product is not accepted under policy B")
        compatibility = audit_config_compatibility(parent["config"], config)
        for name, expected in parent["files"].items():
            if Path(name).name != name or sha256(prepared / name) != expected:
                raise ValueError(f"H1 product hash mismatch: {name}")
        end = utc_ms(config.data.validation_start)
        details = {}
        for name, column in TABLES.items():
            lower = utc_ms(config.data.warmup_start) if name in {
                "bars.csv", "observations.csv", "features.csv"
            } else utc_ms(config.data.train_start)
            details[name] = _export_prefix(prepared / name, stage / name, column, lower, end)
        for name in METADATA:
            (stage / name).write_bytes((prepared / name).read_bytes())
        for name, column in TABLES.items():
            compared = _audit_prefix(prepared / name, stage / name, column, end,
                                     details[name]["rows"])
            details[name].update(prefix_equal_row_by_row=True, audited_rows=compared)
        for name in METADATA:
            if sha256(stage / name) != parent["files"][name]:
                raise ValueError(f"H1 metadata copy mismatch: {name}")
        manifest = dict(
            schema_version="p2r_training_shard_v1",
            status="accepted_for_p2r_training_only",
            parent_h1_manifest_sha256=expected_manifest,
            parent_h1_file_sha256=parent["files"],
            train_start_ms=utc_ms(config.data.train_start),
            train_end_exclusive_ms=end,
            files={name: sha256(stage / name) for name in (*TABLES, *METADATA)},
            derivation="byte_exact_h1_training_prefix_v1",
        )
        _write_json(stage / "manifest.json", manifest)
        manifest_sha = sha256(stage / "manifest.json")
        checks = _audit_training(config, prepared, stage, expected_manifest, manifest_sha)
        report = dict(status="passed", checked_utc=datetime.now(timezone.utc).isoformat(),
                      parent_manifest_sha256=expected_manifest,
                      training_shard_manifest_sha256=manifest_sha,
                      config_compatibility=compatibility,
                      original_file_hashes_verified=parent["files"],
                      files=details, **checks,
                      historical_training_executed=False,
                      validation_observations_used_for_learning_or_diagnostics=False,
                      final_test_accessed=False)
        _write_json(stage / "export-audit.json", report)
        if output.exists():
            raise FileExistsError(output)
        os.rename(stage, output)
        return report
    except BaseException as exc:
        manifest_path = stage / "manifest.json"
        if manifest_path.exists():
            entry = json.loads(manifest_path.read_text())
            entry["status"] = "failed"
            manifest_path.write_text(json.dumps(entry, indent=2, sort_keys=True) + "\n")
        (stage / "failure.json").write_text(json.dumps(
            dict(status="failed", error=f"{type(exc).__name__}: {exc}"), indent=2) + "\n")
        raise
