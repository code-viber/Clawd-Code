"""Tests for the coin change solution."""

from __future__ import annotations

import unittest

from src.algorithms.coin_change import Solution, coin_change


class TestCoinChange(unittest.TestCase):
    """Validate minimum-coin dynamic programming behavior."""

    def test_example_uses_fewest_coins(self):
        self.assertEqual(Solution().coinChange([1, 2, 5], 11), 3)

    def test_unreachable_amount_returns_negative_one(self):
        self.assertEqual(Solution().coinChange([2], 3), -1)

    def test_zero_amount_requires_zero_coins(self):
        self.assertEqual(Solution().coinChange([1], 0), 0)

    def test_functional_wrapper_matches_solution(self):
        self.assertEqual(coin_change([1, 3, 4], 6), 2)


if __name__ == "__main__":
    unittest.main()

