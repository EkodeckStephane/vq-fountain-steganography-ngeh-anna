from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run_distribution_sampler_probe import (
    anchor_values,
    geometry_candidates,
    map_position_for_crop,
    map_position_for_crop_transform,
    scheduled_positions,
    token_jsd_to_prior,
    token_block_groups,
)


class DistributionProbeTests(unittest.TestCase):
    def test_center_positions_respect_margin(self) -> None:
        positions = scheduled_positions(tokens_per_side=8, mode="center", margin=2, seed="unit")
        self.assertEqual(len(positions), 16)
        self.assertEqual(positions, scheduled_positions(tokens_per_side=8, mode="center", margin=2, seed="unit"))
        for position in positions:
            row, col = divmod(position, 8)
            self.assertGreaterEqual(row, 2)
            self.assertLess(row, 6)
            self.assertGreaterEqual(col, 2)
            self.assertLess(col, 6)

    def test_random_positions_are_keyed_permutation(self) -> None:
        positions = scheduled_positions(tokens_per_side=4, mode="random", margin=0, seed="unit")
        self.assertEqual(sorted(positions), list(range(16)))
        self.assertEqual(positions, scheduled_positions(tokens_per_side=4, mode="random", margin=0, seed="unit"))
        self.assertNotEqual(positions, list(range(16)))

    def test_crop_mapping_moves_inner_positions_outward(self) -> None:
        self.assertEqual(map_position_for_crop(5 * 16 + 5, tokens_per_side=16, crop_ratio=1.0), 5 * 16 + 5)
        mapped = map_position_for_crop(2 * 16 + 2, tokens_per_side=16, crop_ratio=0.9)
        self.assertIsNotNone(mapped)
        row, col = divmod(int(mapped), 16)
        self.assertLess(row, 2)
        self.assertLess(col, 2)

    def test_crop_mapping_supports_offset_geometry(self) -> None:
        centered = map_position_for_crop_transform(
            5 * 16 + 5,
            tokens_per_side=16,
            crop_ratio=0.9,
            row_offset=0.0,
            col_offset=0.0,
        )
        shifted = map_position_for_crop_transform(
            5 * 16 + 5,
            tokens_per_side=16,
            crop_ratio=0.9,
            row_offset=0.02,
            col_offset=-0.02,
        )
        self.assertIsNotNone(centered)
        self.assertIsNotNone(shifted)
        self.assertNotEqual(centered, shifted)

    def test_geometry_candidates_expand_offsets_only_for_2d_search(self) -> None:
        self.assertEqual(geometry_candidates("none", [0.9], [-0.01, 0.0]), [(1.0, 0.0, 0.0)])
        self.assertEqual(geometry_candidates("anchors", [0.9], [-0.01, 0.0]), [(0.9, 0.0, 0.0)])
        candidates = geometry_candidates("anchors2d", [0.9], [-0.01, 0.0])
        self.assertEqual(len(candidates), 4)
        self.assertIn((0.9, -0.01, 0.0), candidates)

    def test_anchor_values_are_deterministic_and_bounded(self) -> None:
        first = anchor_values(16, bits_per_token=2, seed="unit")
        second = anchor_values(16, bits_per_token=2, seed="unit")
        self.assertEqual(first, second)
        self.assertEqual(len(first), 16)
        self.assertTrue(all(0 <= value < 4 for value in first))

    def test_token_jsd_to_prior_is_zero_for_matching_histogram(self) -> None:
        self.assertAlmostEqual(token_jsd_to_prior([0, 1], np.array([0.5, 0.5])), 0.0)

    def test_token_block_groups_partition_center_positions(self) -> None:
        groups = token_block_groups(tokens_per_side=8, mode="center", margin=2, token_block_size=2, seed="unit")
        self.assertEqual(len(groups), 4)
        self.assertTrue(all(len(group) == 4 for group in groups))
        flattened = sorted(position for group in groups for position in group)
        expected = sorted(scheduled_positions(tokens_per_side=8, mode="center", margin=2, seed="other"))
        self.assertEqual(flattened, expected)
        for position in flattened:
            row, col = divmod(position, 8)
            self.assertGreaterEqual(row, 2)
            self.assertLess(row, 6)
            self.assertGreaterEqual(col, 2)
            self.assertLess(col, 6)


if __name__ == "__main__":
    unittest.main()
