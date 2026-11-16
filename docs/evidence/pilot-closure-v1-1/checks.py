"""Synthetic boundary checks and a read-only input audit for the v1.1 proposal."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cpcv_index_audit as index_audit


class SyntheticIndexChecks(unittest.TestCase):
    def test_information_overlap_is_half_open(self) -> None:
        first_2021 = index_audit.year_start(2021)
        self.assertFalse(index_audit.overlaps(
            first_2021 - index_audit.STEP, first_2021, (2021,)
        ))
        self.assertTrue(index_audit.overlaps(
            first_2021 - index_audit.STEP, first_2021 + 1, (2021,)
        ))
        self.assertTrue(index_audit.overlaps(
            first_2021, first_2021 + index_audit.STEP, (2021,)
        ))

    def test_post_test_embargo_excludes_only_its_half_open_interval(self) -> None:
        end_2021 = index_audit.year_start(2022)
        limit = end_2021 + 180 * index_audit.STEP
        self.assertFalse(index_audit.post_test_embargo(end_2021 - 1, (2021,), 180))
        self.assertTrue(index_audit.post_test_embargo(end_2021, (2021,), 180))
        self.assertTrue(index_audit.post_test_embargo(limit - 1, (2021,), 180))
        self.assertFalse(index_audit.post_test_embargo(limit, (2021,), 180))

    def test_index_rejects_hash_mismatch_and_non_train_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=("partition", "value"))
                writer.writeheader()
                writer.writerow({"partition": "train", "value": "1"})
            expected = index_audit.digest(path)
            self.assertEqual(len(index_audit.read_index(
                path, expected, ("partition", "value")
            )), 1)
            with self.assertRaisesRegex(ValueError, "Index hash mismatch"):
                index_audit.read_index(path, "0" * 64, ("partition", "value"))
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=("partition", "value"))
                writer.writeheader()
                writer.writerow({"partition": "validation", "value": "1"})
            with self.assertRaisesRegex(ValueError, "Non-training index"):
                index_audit.read_index(
                    path, index_audit.digest(path), ("partition", "value")
                )


class AcceptedMetadataChecks(unittest.TestCase):
    def test_audit_opens_only_six_allowed_metadata_and_index_files(self) -> None:
        allowed = {
            (index_audit.SHARD / "manifest.json").resolve(),
            (index_audit.H1 / "manifest.json").resolve(),
            (index_audit.SHARD / "episodes.csv").resolve(),
            (index_audit.SHARD / "transitions.csv").resolve(),
            (index_audit.H1 / "fit_observations.csv").resolve(),
            (index_audit.ROOT / "docs/evidence/p3-market-2026-10-13/final-closure.json").resolve(),
        }
        opened: set[Path] = set()
        original = Path.open

        def guarded_open(path: Path, *args: object, **kwargs: object):
            resolved = path.resolve()
            self.assertIn(resolved, allowed)
            opened.add(resolved)
            return original(path, *args, **kwargs)

        with patch.object(Path, "open", guarded_open):
            result = index_audit.audit()
        self.assertEqual(opened, allowed)
        self.assertEqual(set(result["inputs_opened"]), {
            str(path.relative_to(index_audit.ROOT)) for path in allowed
        })
        self.assertEqual(result["training_index_counts"]["episode_starts"], 7048)
        self.assertEqual(result["cpcv"]["split_count"], 10)
        self.assertEqual(result["cpcv"]["nominal_paths"], 4)
        self.assertEqual(len(result["cpcv"]["splits"]), 10)
        self.assertEqual(
            result["sortino_precision_sensitivity"]
            ["normal_approx_n_for_80pct_power_one_sided_alpha_0_025"]["1.0"], 32
        )


if __name__ == "__main__":
    unittest.main()
