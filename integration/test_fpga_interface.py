"""
Tests for integration/fpga_interface.py.

This is a software-only test for now. It proves that the new interface
returns the same result as the independent direct modulo oracle.

Later, the exact same test can run with the real FPGA backend.
"""

import random

from integration.fpga_interface import fpga_hrr


Q = 3329


def test_known_cases() -> None:
    cases = [
        (0, 0),
        (0, 3328),
        (1, 1),
        (1, 3328),
        (3328, 1),
        (3328, 3328),
        (123, 456),
        (1000, 2000),
    ]

    for a, b in cases:
        expected = (a * b) % Q
        actual = fpga_hrr(a, b)
        assert actual == expected, (
            f"Mismatch: a={a}, b={b}, actual={actual}, expected={expected}"
        )


def test_random_cases() -> None:
    random.seed(20260921)

    for _ in range(1000):
        a = random.randrange(Q)
        b = random.randrange(Q)

        expected = (a * b) % Q
        actual = fpga_hrr(a, b)

        assert actual == expected, (
            f"Mismatch: a={a}, b={b}, actual={actual}, expected={expected}"
        )


def test_invalid_inputs() -> None:
    bad_cases = [
        (-1, 0),
        (0, -1),
        (Q, 0),
        (0, Q),
    ]

    for a, b in bad_cases:
        try:
            fpga_hrr(a, b)
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"Expected ValueError for a={a}, b={b}"
            )


if __name__ == "__main__":
    test_known_cases()
    test_random_cases()
    test_invalid_inputs()
    print("FPGA interface software-fallback tests: ALL PASSED")
