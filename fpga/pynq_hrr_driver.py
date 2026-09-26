"""
Real PYNQ MMIO backend for the HRR accelerator, matching hrr_axi.v's
register map:

    0x00  A       [11:0]  operand a
    0x04  B       [11:0]  operand b
    0x08  CONTROL [0]     START (write 1; wrapper self-clears the pulse)
    0x0C  STATUS  [0]     DONE (sticky until next START)  [1] BUSY
    0x10  RESULT  [11:0]  valid once DONE=1

Drop this next to fpga_interface.py on the PYNQ-Z2 and swap the current
software fallback (hrr_reference.py) for HrrAccelerator.fpga_hrr(a, b)
once the bitstream from build_hrr_axi_project.tcl is loaded.
"""

import time
from pynq import Overlay, MMIO


REG_A = 0x00
REG_B = 0x04
REG_CONTROL = 0x08
REG_STATUS = 0x0C
REG_RESULT = 0x10

CONTROL_START = 0x1
STATUS_DONE = 0x1
STATUS_BUSY = 0x2

Q = 3329


class HrrAccelerator:
    """Thin MMIO wrapper around one hrr_axi instance."""

    def __init__(self, bitstream_path="hrr_bd_wrapper.bit", ip_name=None,
                 base_addr=None, addr_range=0x10000, timeout_s=0.01):
        """
        Two ways to locate the peripheral:

        - Pass `ip_name` matching the block-design instance name (e.g.
          "hrr_axi_0") and let the .hwh metadata resolve the address —
          this is the normal PYNQ overlay flow.
        - Or pass an explicit `base_addr` (the value build_hrr_axi_project.tcl
          prints for hrr_axi_0) if you're driving the peripheral directly
          without an overlay's IP_DICT.
        """
        self.timeout_s = timeout_s

        if ip_name is not None:
            self.overlay = Overlay(bitstream_path)
            self.mmio = getattr(self.overlay, ip_name).mmio
        elif base_addr is not None:
            # Still need the bitstream loaded once; this path skips the
            # overlay's driver lookup and talks to the register file
            # directly at a known physical address.
            self.overlay = Overlay(bitstream_path)
            self.mmio = MMIO(base_addr, addr_range)
        else:
            raise ValueError("Provide either ip_name or base_addr")

    def fpga_hrr(self, a: int, b: int) -> int:
        """r = (a * b) mod 3329, computed on the FPGA HRR core."""
        if not (0 <= a < Q) or not (0 <= b < Q):
            raise ValueError(f"a, b must be in [0, {Q}); got a={a}, b={b}")

        self.mmio.write(REG_A, a)
        self.mmio.write(REG_B, b)
        self.mmio.write(REG_CONTROL, CONTROL_START)

        deadline = time.time() + self.timeout_s
        while True:
            status = self.mmio.read(REG_STATUS)
            if status & STATUS_DONE:
                break
            if time.time() > deadline:
                raise TimeoutError(
                    f"HRR core did not assert DONE within {self.timeout_s}s "
                    f"(last STATUS=0x{status:02x}, BUSY={bool(status & STATUS_BUSY)})"
                )

        return self.mmio.read(REG_RESULT) & 0xFFF

    def self_check(self, n_random: int = 100) -> bool:
        """Cross-check the FPGA result against the direct % Q oracle,
        the same invariant the Python reference tests already use."""
        import random

        for a, b in [(0, 0), (1, 1), (Q - 1, Q - 1), (Q - 1, 1), (1, Q - 1)]:
            if self.fpga_hrr(a, b) != (a * b) % Q:
                return False
        for _ in range(n_random):
            a, b = random.randrange(Q), random.randrange(Q)
            if self.fpga_hrr(a, b) != (a * b) % Q:
                return False
        return True


if __name__ == "__main__":
    # Example: adjust ip_name to whatever the block design calls the
    # instance (default in build_hrr_axi_project.tcl is "hrr_axi_0").
    acc = HrrAccelerator(bitstream_path="hrr_bd_wrapper.bit", ip_name="hrr_axi_0")
    print("Self-check passed:", acc.self_check())
    print("fpga_hrr(7, 9) =", acc.fpga_hrr(7, 9))
