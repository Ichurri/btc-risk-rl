import json
from urllib.parse import parse_qs, urlparse

from conftest import synthetic_rows
from test_data import make_transport

from btc_risk_rl.config import STEP_MS, utc_ms
from btc_risk_rl.data.binance import fetch_development, sha256
from btc_risk_rl.data.recheck import recheck_anomalies


def test_recheck_preserves_raw_and_records_persistent_gap(config, tmp_path):
    raw = tmp_path / "raw"
    transport, _ = make_transport(config, remove=300)
    fetch_development(config, raw, transport)
    before = sha256(raw / "manifest.json")
    audit = recheck_anomalies(config, raw, tmp_path / "audit", lambda _: b"[]")
    assert audit["counts"] == {"still_missing": 1}
    assert before == sha256(raw / "manifest.json")
    assert not audit["final_test_accessed"]


def test_recheck_records_recovered_bar_without_replacement(config, tmp_path):
    raw = tmp_path / "raw"
    transport, _ = make_transport(config, remove=300)
    fetch_development(config, raw, transport)

    def recovery(url):
        q = parse_qs(urlparse(url).query)
        t = int(q["startTime"][0])
        assert t + STEP_MS <= utc_ms(config.data.test_start)
        return json.dumps(synthetic_rows(t, 1)).encode()

    audit = recheck_anomalies(config, raw, tmp_path / "audit", recovery)
    assert audit["counts"] == {"changed": 1}
    assert audit["original_data_modified"] is False
