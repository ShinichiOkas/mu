"""簡易統計モジュール（バグあり）。test_stats.py を通るように修正すること。"""


def mean(xs):
    if not xs:
        return 0
    return sum(xs) / len(xs)


def median(xs):
    if not xs:
        return 0
    s = sorted(xs)
    return s[len(s) // 2]


def variance(xs):
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def value_range(xs):
    return max(xs)
