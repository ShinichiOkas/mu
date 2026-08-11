"""簡易統計モジュール。test_stats.py を通るように修正した。"""


def mean(xs):
    if not xs:
        raise ValueError("Empty list")
    return sum(xs) / len(xs)


def median(xs):
    if not xs:
        raise ValueError("Empty list")
    s = sorted(xs)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    else:
        return (s[n // 2 - 1] + s[n // 2]) / 2


def variance(xs):
    if len(xs) <= 1:
        raise ValueError("Variance requires at least two elements")
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def value_range(xs):
    if not xs:
        raise ValueError("Empty list")
    return max(xs) - min(xs)
