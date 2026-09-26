"""
Tests for hrr_reference.py.

The direct expression (a*b) % q is used ONLY as an independent oracle.
It is not part of the HRR implementation.
"""

import random

from hrr.hrr_reference import Q, hrr


def test_boundary_cases():
    cases = [
        (0, 0),
        (0, Q - 1),
        (1, 1),
        (1, Q - 1),
        (Q - 1, 1),
        (Q - 1, Q - 1),
    ]

    for a, b in cases:
        result = hrr(a, b)
        expected = (a * b) % Q
        assert result == expected, (
            f"Boundary failure: a={a}, b={b}, "
            f"result={result}, expected={expected}"
        )


def test_known_cases():
    cases = [
        (100, 200),
        (1000, 2000),
        (3000, 2000),
        (1234, 2345),
        (3327, 3326),
    ]

    for a, b in cases:
        result = hrr(a, b)
        expected = (a * b) % Q
        assert result == expected, (
            f"Known-case failure: a={a}, b={b}, "
            f"result={result}, expected={expected}"
        )


def test_randomized_cases(num_tests=10000, seed=20260919):
    rng = random.Random(seed)

    for _ in range(num_tests):
        a = rng.randrange(Q)
        b = rng.randrange(Q)

        result = hrr(a, b)
        expected = (a * b) % Q

        assert result == expected, (
            f"Random failure: a={a}, b={b}, "
            f"result={result}, expected={expected}"
        )


def main():
    print("=" * 55)
    print("HRR REFERENCE MODEL TEST")
    print("=" * 55)

    test_boundary_cases()
    print("Boundary cases: PASS")

    test_known_cases()
    print("Known cases: PASS")

    num_random = 10000
    test_randomized_cases(num_random)
    print(f"Randomized cases ({num_random}): PASS")

    print("=" * 55)
    print("ALL TESTS PASSED")
    print("=" * 55)


if __name__ == "__main__":
    main()
