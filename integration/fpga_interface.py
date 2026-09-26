"""
FPGA interface for the Smart Meter project.

Current stage:
    - Runs on the laptop/Windows development machine.
    - Uses the verified Python HRR reference as a fallback.
    - Keeps the application-facing API stable so we can later replace
      the fallback with the real PYNQ/AXI backend.

Future stage:
    Python on PYNQ-Z2 ARM
        -> AXI/MMIO
        -> FPGA HRR
        -> AXI/MMIO
        -> Python
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

# When this file is run/imported from the integration/ folder, add the
# project root so that the sibling hrr/ package can be imported.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from hrr.hrr_reference import hrr


@dataclass
class FPGAInterface:
    """
    Application-facing HRR interface.

    At the moment, hardware_available=False means the verified software
    reference is used. When the Vivado AXI design is ready, this same class
    will gain a hardware backend without changing the rest of the project.
    """

    hardware_available: bool = False

    def hrr(self, a: int, b: int) -> int:
        """
        Compute (a*b) mod 3329.

        Current behavior:
            software fallback -> hrr_reference.hrr()

        Future behavior:
            hardware_available=True
                -> AXI/MMIO write a
                -> AXI/MMIO write b
                -> AXI/MMIO start
                -> wait for done
                -> read result
        """
        self._validate_operands(a, b)

        if self.hardware_available:
            return self._hrr_hardware(a, b)

        return hrr(a, b)

    @staticmethod
    def _validate_operands(a: int, b: int) -> None:
        if not isinstance(a, int) or not isinstance(b, int):
            raise TypeError("a and b must be integers")

        if not 0 <= a < 3329:
            raise ValueError("a must satisfy 0 <= a < 3329")

        if not 0 <= b < 3329:
            raise ValueError("b must satisfy 0 <= b < 3329")

    def _hrr_hardware(self, a: int, b: int) -> int:
        """
        Placeholder for the real PYNQ AXI implementation.

        We intentionally do not invent register addresses before the
        Vivado AXI design defines them.
        """
        raise RuntimeError(
            "FPGA hardware backend is not configured yet. "
            "Wait for the Vivado AXI register map, then connect it here."
        )


# Simple application-level function.
# Your smart-meter/crypto code can call this without knowing whether
# HRR is running in software or hardware.
_default_interface = FPGAInterface(hardware_available=False)


def fpga_hrr(a: int, b: int) -> int:
    """Return (a*b) mod 3329 using the current HRR backend."""
    return _default_interface.hrr(a, b)
