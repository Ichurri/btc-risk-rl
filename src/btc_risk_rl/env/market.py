"""Immutable development-only paths; timestamps label four-hour bar opens."""

from dataclasses import dataclass

import numpy as np

from btc_risk_rl.config import STEP_MS, guard_development
from btc_risk_rl.data.segmented_audit import verify_segmented


@dataclass(frozen=True)
class MarketPath:
    times: np.ndarray
    opens: np.ndarray
    closes: np.ndarray
    features: np.ndarray
    partition: str
    segment_id: int
    end_reason: str
    provenance: str

    def __post_init__(self):
        times = np.asarray(self.times)
        if times.ndim != 1 or len(times) < 2 or not np.issubdtype(times.dtype, np.integer):
            raise ValueError("Path requires integral timestamps and at least one transition")
        if times[0] % STEP_MS or not (np.diff(times) == STEP_MS).all():
            raise ValueError("Path cannot cross interruptions or unaligned bars")
        guard_development(int(times[0]), int(times[-1]) + STEP_MS)
        if self.partition not in {"train", "validation"}:
            raise ValueError("Only development partitions are supported")
        if self.end_reason not in {"collection_window", "segment_boundary", "partition_boundary"}:
            raise ValueError("Unknown path boundary")
        for name, shape, dtype in [
            ("times", (len(times),), np.int64),
            ("opens", (len(times),), np.float64),
            ("closes", (len(times),), np.float64),
            ("features", (len(times), 10), np.float64),
        ]:
            array = np.array(getattr(self, name), dtype=dtype, copy=True)
            if array.shape != shape or not np.isfinite(array).all():
                raise ValueError(f"Invalid {name} shape or values")
            if name in {"opens", "closes"} and (array <= 0).any():
                raise ValueError("Prices must be positive")
            array.setflags(write=False)
            object.__setattr__(self, name, array)


class AcceptedMarket:
    """Audit once, then select only paths from the accepted temporal indices."""

    def __init__(self, config, raw, prepared, diagnosis=None):
        import json

        import pandas as pd

        from btc_risk_rl.data.binance import sha256
        from btc_risk_rl.data.segmented_pipeline import DIAGNOSIS

        manifest = json.loads((prepared / "manifest.json").read_text())
        if manifest["status"] != "accepted":
            raise ValueError("Simulator requires an accepted dataset")
        source = json.loads((raw / "manifest.json").read_text())
        guard_development(source["start_inclusive_ms"], source["end_exclusive_ms"])
        self.audit = verify_segmented(
            config, raw, prepared, DIAGNOSIS if diagnosis is None else diagnosis
        )
        self.manifest_sha256 = sha256(prepared / "manifest.json")
        self._config = config
        tables = {}
        for name in ("bars.csv", "observations.csv", "episodes.csv", "transitions.csv"):
            tables[name] = pd.read_csv(prepared / name, float_precision="round_trip")
            if sha256(prepared / name) != manifest["files"][name]:
                raise ValueError("Product changed during simulator loading")
        self._bars = tables["bars.csv"].set_index("open_time")
        self._observations = tables["observations.csv"].set_index("open_time")
        self._episodes = tables["episodes.csv"].set_index("episode_id")
        self._transitions = tables["transitions.csv"]
        self.episode_ids = tuple(int(i) for i in self._episodes.index)
        self._target_keys = {
            (r.partition, int(r.segment_id), int(r.target_ms))
            for r in self._transitions.itertuples()
        }

    @classmethod
    def training_only(cls, config, prepared, *, expected_manifest):
        from btc_risk_rl.env.training_view import load_training_view

        return load_training_view(cls, config, prepared, expected_manifest)

    def _path(self, first, last, partition, segment_id):
        from btc_risk_rl.config import utc_ms
        from btc_risk_rl.features.market import FEATURES

        times = np.arange(first - STEP_MS, last + STEP_MS, STEP_MS, dtype=np.int64)
        if not all((partition, segment_id, int(t)) in self._target_keys for t in times[1:]):
            raise ValueError("Path crosses an exclusion or partition")
        bars = self._bars.loc[times]
        obs = self._observations.loc[times]
        if not (bars.segment_id == segment_id).all() or not (obs.segment_id == segment_id).all():
            raise ValueError("Path crosses a segment")
        end = utc_ms(
            self._config.data.validation_start
            if partition == "train"
            else self._config.data.test_start
        )
        reason = (
            "partition_boundary"
            if last + STEP_MS == end
            else "segment_boundary"
            if (partition, segment_id, last + STEP_MS) not in self._target_keys
            else "collection_window"
        )
        return MarketPath(
            times,
            bars.open.to_numpy(),
            bars.close.to_numpy(),
            obs[FEATURES].to_numpy(),
            partition,
            segment_id,
            reason,
            "accepted_policy_B:" + self.manifest_sha256,
        )

    def training_path(self, episode_id):
        if (
            isinstance(episode_id, bool)
            or not isinstance(episode_id, (int, np.integer))
            or episode_id not in self._episodes.index
        ):
            raise ValueError("Unknown indexed episode")
        row = self._episodes.loc[episode_id]
        return self._path(
            int(row.first_target_ms), int(row.last_target_ms), "train", int(row.segment_id)
        )

    def validation_path(self):
        if getattr(self, "_training_only", False):
            raise ValueError("Validation is inaccessible in the training view")
        rows = self._transitions.loc[self._transitions.partition == "validation"]
        return self._path(
            int(rows.iloc[0].target_ms),
            int(rows.iloc[-1].target_ms),
            "validation",
            int(rows.iloc[0].segment_id),
        )
