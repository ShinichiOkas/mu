"""簡易統計モジュール（バグあり）。test_stats.py を通るように修正すること。"""


def mean(xs):
    if not xs:
        raise ValueError("Empty list provided for mean calculation.")
    return sum(xs) / len(xs)


def median(xs):
    if not xs:
        raise ValueError("Empty list provided for median calculation.")
    s = sorted(xs)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    else:
        return (s[n // 2 - 1] + s[n // 2]) / 2


def variance(xs):
    if len(xs) < 2:
        raise ValueError("At least two elements are required for sample variance.")
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def value_range(xs):
    if not xs:
        raise ValueError("Empty list provided for range calculation.")
    return max(xs) - min(xs)


if __name__ == "__main__":
    try:
        # Example checks to ensure basic functionality
        mean([1, 2, 3])
        median([1, 2, 3, 4])
        variance([1, 2, 3])
        value_range([10, 20, 30])
        print("CALCULATION SUCCESSFUL")
    except Exception:
        pass
