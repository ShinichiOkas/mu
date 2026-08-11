"""stats の仕様を定めるテスト。このファイルは変更禁止（読み取り専用）。"""
import unittest

from buggy_stats import mean, median, variance, value_range


class TestStats(unittest.TestCase):
    def test_mean(self):
        self.assertAlmostEqual(mean([1, 2, 3, 4]), 2.5)

    def test_mean_empty_raises(self):
        with self.assertRaises(ValueError):
            mean([])

    def test_median_odd(self):
        self.assertEqual(median([3, 1, 2]), 2)

    def test_median_even_is_average_of_middle_two(self):
        self.assertAlmostEqual(median([1, 2, 3, 4]), 2.5)

    def test_median_empty_raises(self):
        with self.assertRaises(ValueError):
            median([])

    def test_variance_is_sample_variance(self):
        # 標本分散（n-1 で割る）
        self.assertAlmostEqual(variance([1, 2, 3, 4]), 5 / 3)

    def test_variance_single_raises(self):
        with self.assertRaises(ValueError):
            variance([5])

    def test_value_range(self):
        self.assertEqual(value_range([4, 1, 7]), 6)

    def test_value_range_empty_raises(self):
        with self.assertRaises(ValueError):
            value_range([])


if __name__ == "__main__":
    unittest.main()
