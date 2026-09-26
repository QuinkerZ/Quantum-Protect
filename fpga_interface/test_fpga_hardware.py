"""
Physical PYNQ-Z2 test for fpga_interface/fpga_interface.py.

Run from the QuantumSecurity project root:

    python3 -m fpga_interface.test_fpga_hardware
"""

import random

from fpga_interface.fpga_interface import FPGAInterface


Q = 3329


def main() -> None:
    print("Initializing FPGA HRR backend...")

    fpga = FPGAInterface(
        hardware_available=True,
        bitstream_path="/home/xilinx/jupyter_notebooks/hrr_bd_wrapper.bit",
        ip_name="hrr_axi_0",
        timeout_s=0.1,
    )

    print("FPGA backend initialized.")
    print("Testing known cases...")

    known_cases = [
        (0, 0),
        (1, 1),
        (1, Q - 1),
        (Q - 1, 1),
        (Q - 1, Q - 1),
        (7, 9),
        (123, 456),
        (3328, 3327),
    ]

    for a, b in known_cases:
        actual = fpga.hrr(a, b)
        expected = (a * b) % Q

        assert actual == expected, (
            f"FAIL: ({a}, {b}) -> FPGA={actual}, expected={expected}"
        )

        print(f"  PASS: ({a}, {b}) -> {actual}")

    print()

    print("Testing 100 randomized cases...")

    random.seed(20260922)

    for _ in range(100):
        a = random.randrange(Q)
        b = random.randrange(Q)

        actual = fpga.hrr(a, b)
        expected = (a * b) % Q

        assert actual == expected, (
            f"FAIL: ({a}, {b}) -> FPGA={actual}, expected={expected}"
        )

    print("  PASS: 100/100 randomized cases")
    print()
    print("FPGA HRR INTERFACE TEST: ALL PASSED")


if __name__ == "__main__":
    main()