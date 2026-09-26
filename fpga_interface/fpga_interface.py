"""
Application-facing HRR interface.

Backends:
- Software reference: hrr.hrr_reference.hrr
- PYNQ FPGA: hrr_axi_0 via AXI4-Lite/MMIO

The default remains software so the existing laptop tests continue to work.
On the PYNQ-Z2, explicitly enable the hardware backend:

    fpga = FPGAInterface(hardware_available=True)
    print(fpga.hrr(7, 9))

or:

    fpga = FPGAInterface.from_environment()

Set:
    QUANTUM_FPGA=1

Optional:
    HRR_BITSTREAM=/home/xilinx/jupyter_notebooks/hrr_bd_wrapper.bit
    HRR_IP_NAME=hrr_axi_0
    HRR_TIMEOUT_S=0.1
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from hrr.hrr_reference import hrr


Q = 3329

REG_A = 0x00
REG_B = 0x04
REG_CONTROL = 0x08
REG_STATUS = 0x0C
REG_RESULT = 0x10

CONTROL_START = 0x1
STATUS_DONE = 0x1
STATUS_BUSY = 0x2


@dataclass
class FPGAInterface:
    """
    Stable application-facing HRR API.

    hardware_available=False:
        Use the software HRR reference.

    hardware_available=True:
        Load the PYNQ overlay and use hrr_axi_0 through MMIO.
    """

    hardware_available: bool = False
    bitstream_path: str = str(PROJECT_ROOT / "fpga" / "hrr_bd_wrapper.bit")
    ip_name: str = "hrr_axi_0"
    timeout_s: float = 0.1

    def __post_init__(self) -> None:
        self._ip = None
        self._overlay = None

        if self.hardware_available:
            self._initialize_hardware()

    @classmethod
    def from_environment(cls) -> "FPGAInterface":
        """
        Select the backend from QUANTUM_FPGA.

        QUANTUM_FPGA=1/true/yes/on -> FPGA backend.
        Anything else -> software backend.
        """
        enabled = os.environ.get("QUANTUM_FPGA", "").strip().lower()
        use_fpga = enabled in {"1", "true", "yes", "on"}

        return cls(
            hardware_available=use_fpga,
            bitstream_path=os.environ.get(
                "HRR_BITSTREAM",
                str(PROJECT_ROOT / "fpga" / "hrr_bd_wrapper.bit"),
            ),
            ip_name=os.environ.get("HRR_IP_NAME", "hrr_axi_0"),
            timeout_s=float(os.environ.get("HRR_TIMEOUT_S", "0.1")),
        )

    def _initialize_hardware(self) -> None:
        try:
            from pynq import Overlay
        except ImportError as exc:
            raise RuntimeError(
                "FPGA backend requested, but the PYNQ Python package is not "
                "available. Run this backend on the PYNQ-Z2."
            ) from exc

        bitstream = Path(self.bitstream_path)
        if not bitstream.exists():
            raise FileNotFoundError(
                f"HRR bitstream not found: {bitstream}"
            )

        self._overlay = Overlay(str(bitstream))

        if self.ip_name not in self._overlay.ip_dict:
            raise RuntimeError(
                f"HRR IP '{self.ip_name}' was not found in the loaded overlay. "
                f"Available IPs: {list(self._overlay.ip_dict.keys())}"
            )

        self._ip = getattr(self._overlay, self.ip_name)

        # Confirm the expected hardware address from the HWH metadata.
        phys_addr = self._overlay.ip_dict[self.ip_name]["phys_addr"]
        expected_addr = 0x40000000
        if phys_addr != expected_addr:
            raise RuntimeError(
                f"Unexpected {self.ip_name} base address: "
                f"0x{phys_addr:08X}; expected 0x{expected_addr:08X}"
            )

    def hrr(self, a: int, b: int) -> int:
        """Compute (a*b) mod 3329 using the selected backend."""
        self._validate_operands(a, b)

        if not self.hardware_available:
            return hrr(a, b)

        return self._hrr_hardware(a, b)

    @staticmethod
    def _validate_operands(a: int, b: int) -> None:
        if not isinstance(a, int) or isinstance(a, bool):
            raise TypeError("a and b must be integers")
        if not isinstance(b, int) or isinstance(b, bool):
            raise TypeError("a and b must be integers")

        if not 0 <= a < Q:
            raise ValueError(f"a must satisfy 0 <= a < {Q}")
        if not 0 <= b < Q:
            raise ValueError(f"b must satisfy 0 <= b < {Q}")

    def _hrr_hardware(self, a: int, b: int) -> int:
        if self._ip is None:
            raise RuntimeError("FPGA backend has not been initialized")

        self._ip.write(REG_A, a)
        self._ip.write(REG_B, b)
        self._ip.write(REG_CONTROL, CONTROL_START)

        deadline = time.monotonic() + self.timeout_s

        while True:
            status = self._ip.read(REG_STATUS)

            if status & STATUS_DONE:
                return self._ip.read(REG_RESULT) & 0xFFF

            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"HRR core did not assert DONE within {self.timeout_s}s "
                    f"(STATUS=0x{status:08X}, "
                    f"BUSY={bool(status & STATUS_BUSY)})"
                )


# Keep the existing application-level function.
# Laptop/default execution remains software-only.
_default_interface = FPGAInterface(hardware_available=False)
_hardware_interface: FPGAInterface | None = None


def fpga_hrr(a: int, b: int) -> int:
    """Return (a*b) mod 3329 using the default software backend."""
    return _default_interface.hrr(a, b)


def hardware_hrr(a: int, b: int) -> int:
    """
    Convenience function for the physical PYNQ-Z2 backend.

    This initializes the FPGA backend on first use.
    """
    global _hardware_interface

    if _hardware_interface is None:
        _hardware_interface = FPGAInterface(hardware_available=True)

    return _hardware_interface.hrr(a, b)

