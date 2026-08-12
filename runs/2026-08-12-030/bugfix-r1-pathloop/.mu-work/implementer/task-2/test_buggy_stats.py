import buggy_stats
import math

def test_all():
    # Test mean
    try:
        res = buggy_stats.mean([1, 2, 3, 4])
        assert res == 2.5
    except Exception as e:
        raise AssertionError(f"mean([1, 2, 3, 4]) failed with {e}")

    try:
        buggy_stats.mean([])
    except ValueError:
        pass
    else:
        raise AssertionError("mean([]) should raise ValueError")

    # Test median
    try:
        res = buggy_stats.median([3, 1, 2])
        assert res == 2
    except Exception as e:
        raise AssertionError(f"median([3, 1, 2]) failed with {e}")
    
    try:
        res = buggy_stats.median([1, 2, 3, 4])
        assert res == 2.5
    except Exception as e:
        raise AssertionError(f"median([1, 2, 3, 4]) failed with {e}")

    try:
        buggy_stats.median([])
    except ValueError:
        pass
    else:
        raise AssertionError("median([]) should raise ValueError")

    # Test variance
    # mean is 2.5, sum((x-m)**2) = (1.5^2 + 0.5^2 + 0.5^2 + 1.5^2) = 2.25+0.25+0.25+2.25 = 5
    # variance is 5 / (4-1) = 5/3 approx 1.666...
    try:
        res = buggy_stats.variance([1, 2, 3, 4])
        assert math.isclose(res, 5/3, rel_tol=1e-7)
    except Exception as e:
        raise AssertionError(f"variance([1, 2, 3, 4]) failed with {e}")

    try:
        buggy_stats.variance([1])
    except ValueError:
        pass
    else:
        raise AssertionError("variance([1]) should raise ValueError")

    try:
        buggy_stats.variance([])
    except ValueError:
        pass
    else:
        raise AssertionError("variance([]) should raise ValueError")

    # Test value_range
    try:
        res = buggy_stats.value_range([4, 1, 7])
        assert res == 6
    except Exception as e:
        raise AssertionError(f"value_range([4, 1, 7]) failed with {e}")

    try:
        buggy_stats.value_range([])
    except ValueError:
        pass
    else:
        raise AssertionError("value_range([]) should raise ValueError")

    print("TESTS_PASSED")

if __name__ == "__main__":
    test_all()
