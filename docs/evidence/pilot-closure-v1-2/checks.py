"""Static and algebraic checks for the v1.2 documentary budget."""

from __future__ import annotations

import math
import unittest
from pathlib import Path
from unittest.mock import patch

import costs


class BudgetChecks(unittest.TestCase):
    def test_only_two_versioned_summary_inputs_are_opened(self) -> None:
        allowed = {costs.P3_CLOSURE, costs.V11_AUDIT}
        opened: set[Path] = set()
        original = Path.read_bytes

        def guarded_read_bytes(path: Path) -> bytes:
            self.assertIn(path, allowed)
            opened.add(path)
            return original(path)

        with patch.object(Path, "read_bytes", guarded_read_bytes):
            result = costs.main()
        self.assertEqual(opened, allowed)
        self.assertEqual(result["observed_p3_beta0"]["run_count"], 9)
        self.assertEqual(result["status"], "proposal_not_authorized_no_execution")

    def test_seed_rosters_are_fixed_distinct_and_outside_pilots(self) -> None:
        main = costs.seeds("main", 36)
        forward = costs.seeds("walk-forward", 3)
        self.assertEqual(len(set(main)), 36)
        self.assertEqual(len(set(forward)), 3)
        self.assertFalse(set(main) & set(forward))
        self.assertFalse((set(main) | set(forward)) & costs.HISTORICAL_SEEDS)
        self.assertEqual(main, costs.seeds("main", 36))

    def test_every_budget_respects_daily_global_cap_with_reserve(self) -> None:
        result = costs.main()
        for row in result["budgets"].values():
            self.assertEqual(row["main_training_runs"], row["main_blocks"] * 3)
            self.assertEqual(row["walk_forward_training_runs"],
                             row["walk_forward_blocks_per_cut"] * 2 * 3)
            self.assertEqual(row["aggregate_reserved_seconds"],
                             row["minimum_active_days_if_every_cap_and_scaled_rate_hold"]
                             * costs.DAILY_RESERVE_SECONDS)
            self.assertGreaterEqual(row["unallocated_work_seconds_in_windows"], 0)
            self.assertLess(row["unallocated_work_seconds_in_windows"], costs.WORK_SECONDS)
            self.assertEqual(row["total_daily_windows_seconds"],
                             row["minimum_active_days_if_every_cap_and_scaled_rate_hold"]
                             * costs.DAY_SECONDS)

    def test_precision_scenarios_do_not_claim_uniform_80_percent_power(self) -> None:
        result = costs.main()["sortino_delta_0_5_normal_only"]["36_blocks"]
        self.assertGreater(result["1.0"]["normal_approx_power_for_effect_0_5_first_Holm_threshold"],
                           0.8)
        self.assertLess(result["1.5"]["normal_approx_power_for_effect_0_5_first_Holm_threshold"],
                        0.8)
        self.assertEqual(result["1.5"]["blocks_for_80pct_normal_approx_power"], 71)
        self.assertTrue(math.isclose(
            result["1.0"]["normal_approx_95pct_half_width"], 0.32666066409000893,
        ))


if __name__ == "__main__":
    unittest.main()
