"""Coin change dynamic programming solution."""

from __future__ import annotations


class Solution:
    """LeetCode-style solution container."""

    def coinChange(self, coins: list[int], amount: int) -> int:
        """Return the fewest coins needed to make ``amount``, or -1 if impossible."""
        if amount == 0:
            return 0

        max_coins = amount + 1
        dp = [0] + [max_coins] * amount

        for total in range(1, amount + 1):
            for coin in coins:
                if coin <= total:
                    dp[total] = min(dp[total], dp[total - coin] + 1)

        return -1 if dp[amount] == max_coins else dp[amount]


def coin_change(coins: list[int], amount: int) -> int:
    """Functional wrapper for callers that do not need the LeetCode class shape."""
    return Solution().coinChange(coins, amount)

