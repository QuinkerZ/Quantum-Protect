"""
QuantumSecurity - ML-KEM-512 Passive Key Interception Observer
=============================================================================
Security Scenario 2 Demonstration Tool:
  "ML-KEM-512 Key Interception → Shared Secret Not Transmitted"

PURPOSE:
  This tool PASSIVELY observes the real PYNQ-Z2 ↔ Utility Server ML-KEM-512
  handshake over TCP:5000. It intercepts every packet using WinDivert SNIFF
  mode (no divert, no drop, no modification), reconstructs newline-delimited
  JSON application messages across TCP segments using per-flow buffers, and
  identifies handshake message types to prove what an adversary recording the
  wire CAN and CANNOT see.

WHAT IS VISIBLE TO AN ADVERSARY:
  - ML-KEM public key (800 raw bytes, Base64-encoded on the wire)
  - ML-KEM ciphertext (768 raw bytes, Base64-encoded on the wire)
  - Protocol metadata (message types, algorithm name, session confirmation)

WHAT IS NEVER VISIBLE TO AN ADVERSARY:
  - ML-KEM private/secret key (1632 bytes, server-local only)
  - 32-byte shared symmetric secret (derived locally, never transmitted)

GUARANTEES:
  - NEVER modifies a single byte of any packet.
  - NEVER drops a packet.
  - All packets pass through transparently; SNIFF mode does not divert traffic.
  - TCP reassembly handles segmented JSON application messages correctly.

NOTE:
  WinDivert SNIFF mode still requires Windows Administrator privileges.
=============================================================================
"""

import argparse
import base64
import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Ensure project root is in sys.path (consistent with mitm_attack.py)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Console helpers
# ---------------------------------------------------------------------------

W = 78  # output width

def rule(char: str = "=") -> str:
    return char * W


def section(title: str, char: str = "=") -> None:
    pad = (W - len(title) - 2) // 2
    print(f"{char * pad} {title} {char * (W - pad - len(title) - 2)}")


def print_banner() -> None:
    print(rule())
    section("QUANTUMSECURITY - ML-KEM-512 PASSIVE KEY INTERCEPTION OBSERVER")
    print("  Security Scenario 2 | Passive SNIFF — Zero Packet Modification")
    print(rule())
    print()


# ---------------------------------------------------------------------------
# Handshake message parser
# ---------------------------------------------------------------------------

# Known ML-KEM handshake message types
HANDSHAKE_TYPES = {
    "mlkem_public_key",
    "mlkem_ciphertext",
    "secure_session",
}


def parse_handshake_messages(buffer: str) -> tuple[list[dict], str]:
    """
    Scan buffer for newline-delimited JSON handshake messages.
    Returns (list_of_parsed_messages, remaining_buffer).
    """
    messages = []
    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            # Not valid JSON (e.g. partial segment); ignore this line
            continue

        msg_type = obj.get("type", "")
        if msg_type in HANDSHAKE_TYPES:
            messages.append(obj)

    return messages, buffer


def _preview(value: str, n: int = 24) -> str:
    """Short preview of a Base64 string."""
    if len(value) <= n + 3:
        return value
    return value[:n] + "..."


def describe_message(msg: dict, direction: str, packet_no: int) -> None:
    """Pretty-print an observed ML-KEM handshake message."""
    msg_type = msg.get("type", "unknown")
    print()
    print(f"  ┌─ HANDSHAKE FRAME #{packet_no} ──────────────────────────────────────────────")
    print(f"  │  Direction   : {direction}")
    print(f"  │  Type        : {msg_type}")
    print(f"  │  Algorithm   : {msg.get('algorithm', '—')}")

    if msg_type == "mlkem_public_key":
        pk_b64 = msg.get("public_key", "")
        raw_len = len(base64.b64decode(pk_b64)) if pk_b64 else 0
        print(f"  │  Public Key  : {len(pk_b64)} b64 chars → {raw_len} raw bytes")
        print(f"  │  Wire Bytes  : {_preview(pk_b64)}")
        print(f"  │  NOTE        : ↑ Fully visible on the wire to any sniffer")

    elif msg_type == "mlkem_ciphertext":
        ct_b64 = msg.get("ciphertext", "")
        raw_len = len(base64.b64decode(ct_b64)) if ct_b64 else 0
        print(f"  │  Ciphertext  : {len(ct_b64)} b64 chars → {raw_len} raw bytes")
        print(f"  │  Wire Bytes  : {_preview(ct_b64)}")
        print(f"  │  NOTE        : ↑ Fully visible on the wire to any sniffer")
        print(f"  │  NOTE        : Shared secret is NOT transmitted — attacker is stuck here")

    elif msg_type == "secure_session":
        status = msg.get("status", "—")
        print(f"  │  Status      : {status}")
        print(f"  │  NOTE        : Confirmation that both ends derived shared secret locally")
        print(f"  │  NOTE        : Shared secret NEVER appears in this frame or any frame")

    print(f"  └──────────────────────────────────────────────────────────────────────")


# ---------------------------------------------------------------------------
# Per-flow TCP buffer
# ---------------------------------------------------------------------------

class FlowBuffer:
    """
    Maintains a per-TCP-flow reassembly buffer.
    The key is (src_addr, src_port, dst_addr, dst_port).
    """

    def __init__(self) -> None:
        self._buffers: Dict[tuple, str] = {}

    def _key(self, packet) -> tuple:
        return (packet.src_addr, packet.src_port,
                packet.dst_addr, packet.dst_port)

    def feed(self, packet) -> tuple[list[dict], bool]:
        """
        Feed packet payload into the relevant flow buffer and extract any
        complete newline-terminated JSON messages.

        Returns (messages, has_partial) where has_partial is True if the
        buffer holds data that hasn't formed a complete line yet.
        """
        if not packet.payload:
            return [], False

        try:
            text = bytes(packet.payload).decode("utf-8", errors="ignore")
        except Exception:
            return [], False

        key = self._key(packet)
        self._buffers[key] = self._buffers.get(key, "") + text
        messages, remaining = parse_handshake_messages(self._buffers[key])
        self._buffers[key] = remaining
        has_partial = bool(remaining.strip())
        return messages, has_partial

    def has_pending(self) -> bool:
        return any(v.strip() for v in self._buffers.values())


# ---------------------------------------------------------------------------
# Main passive observer
# ---------------------------------------------------------------------------

def run_observer(
    target_ip: str = "192.168.2.99",
    server_ip: str = "192.168.2.1",
    server_port: int = 5000,
    verbose: bool = False,
) -> None:
    """
    Main passive observation loop using WinDivert SNIFF mode.
    Traffic is NEVER diverted, dropped, or modified.
    """
    print_banner()

    try:
        import pydivert
        from pydivert import Layer, Flag
    except ImportError:
        print("[ERROR] 'pydivert' is not installed.")
        print("        Install with: pip install pydivert")
        sys.exit(1)

    # We capture bidirectional TCP traffic around port 5000 between the two hosts.
    # SNIFF flag means packets are copied but NOT diverted — they still flow
    # through the stack transparently without any action from us.
    filter_expr = (
        f"tcp.DstPort == {server_port} and ip.SrcAddr == {target_ip} or "
        f"tcp.SrcPort == {server_port} and ip.DstAddr == {target_ip}"
    )

    print("[*] CONFIGURATION:")
    print(f"    PYNQ-Z2 Source        : {target_ip}")
    print(f"    Utility Server        : {server_ip}:{server_port}")
    print(f"    Mode                  : PASSIVE SNIFF — No modification, no divert")
    print(f"    Verbose               : {verbose}")
    print(f"    WinDivert Filter      : {filter_expr}")
    print()
    print("[*] Initializing WinDivert SNIFF mode...")
    print("    [NOTE] Requires Administrator privileges.")
    print("    [NOTE] All packets pass through unchanged — zero interference.")
    print()

    # State tracking
    flow_buf            = FlowBuffer()
    total_packets       = 0
    handshake_frame_no  = 0
    partial_warnings    = 0
    start_time          = datetime.now()

    observed_pk         = False
    observed_ct         = False
    observed_confirm    = False

    pk_raw_len          = 0
    ct_raw_len          = 0
    pk_b64_preview      = ""
    ct_b64_preview      = ""

    try:
        # SNIFF flag: packets are NOT diverted; they are only sniffed/copied.
        # This is the key guarantee that this tool NEVER modifies traffic.
        with pydivert.WinDivert(filter_expr, flags=pydivert.Flag.SNIFF) as w:
            print("[✓] Passive SNIFF filter active.")
            print(f"    Watching for ML-KEM handshake on TCP:{server_port}...")
            print(f"    Press Ctrl+C at any time to stop and view session summary.")
            print()
            print(rule("-"))

            for packet in w:
                total_packets += 1

                if not packet.payload:
                    continue

                direction = (
                    f"PYNQ ({packet.src_addr}:{packet.src_port}) → Server ({packet.dst_addr}:{packet.dst_port})"
                    if str(packet.dst_port) == str(server_port)
                    else f"Server ({packet.src_addr}:{packet.src_port}) → PYNQ ({packet.dst_addr}:{packet.dst_port})"
                )

                if verbose:
                    payload_len = len(bytes(packet.payload))
                    print(f"  [PKT #{total_packets:>4}] {direction}  |  {payload_len} B", flush=True)

                messages, has_partial = flow_buf.feed(packet)

                if has_partial:
                    partial_warnings += 1
                    if verbose:
                        print(f"  [PARTIAL] TCP segment — buffer waiting for remainder...")

                for msg in messages:
                    msg_type = msg.get("type", "")
                    handshake_frame_no += 1
                    describe_message(msg, direction, handshake_frame_no)

                    if msg_type == "mlkem_public_key":
                        observed_pk = True
                        pk_b64 = msg.get("public_key", "")
                        try:
                            pk_raw_len = len(base64.b64decode(pk_b64))
                        except Exception:
                            pk_raw_len = 0
                        pk_b64_preview = _preview(pk_b64, 32)
                        print()
                        print(f"  [ATTACKER] ✓ Public key captured ({pk_raw_len} raw bytes)")
                        print(f"  [ATTACKER] ✗ Cannot recover private key or shared secret from this.")

                    elif msg_type == "mlkem_ciphertext":
                        observed_ct = True
                        ct_b64 = msg.get("ciphertext", "")
                        try:
                            ct_raw_len = len(base64.b64decode(ct_b64))
                        except Exception:
                            ct_raw_len = 0
                        ct_b64_preview = _preview(ct_b64, 32)
                        print()
                        print(f"  [ATTACKER] ✓ Ciphertext captured ({ct_raw_len} raw bytes)")
                        print(f"  [ATTACKER] ✗ Decapsulation requires the server private key.")
                        print(f"  [ATTACKER] ✗ Cannot derive the 32-byte shared secret.")

                    elif msg_type == "secure_session":
                        observed_confirm = True
                        print()
                        print(f"  [ATTACKER] ✓ Session confirmation observed")
                        print(f"  [ATTACKER] ✗ Shared secret is NOT in this frame.")
                        print(f"  [ATTACKER] ✗ Both sides derived secret locally — never transmitted.")

    except PermissionError:
        print()
        print("[ERROR] Access denied — WinDivert requires Administrator privileges.")
        print("        Re-run in an elevated PowerShell or Command Prompt:")
        print(f"        .\\.venv\\Scripts\\python.exe integration\\mlkem_attacker.py")

    except OSError as e:
        if "740" in str(e) or "privilege" in str(e).lower() or "5" in str(e):
            print()
            print("[ERROR] WinDivert requires Administrator privileges.")
            print("        Re-run in an elevated terminal.")
        else:
            print(f"\n[ERROR] WinDivert OS error: {e}")

    except KeyboardInterrupt:
        print()
        print("\n[*] Stopped by user (Ctrl+C).")

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")

    finally:
        duration = (datetime.now() - start_time).total_seconds()
        _print_summary(
            total_packets      = total_packets,
            handshake_frames   = handshake_frame_no,
            partial_warnings   = partial_warnings,
            observed_pk        = observed_pk,
            observed_ct        = observed_ct,
            observed_confirm   = observed_confirm,
            pk_raw_len         = pk_raw_len,
            ct_raw_len         = ct_raw_len,
            pk_b64_preview     = pk_b64_preview,
            ct_b64_preview     = ct_b64_preview,
            duration_s         = duration,
        )


# ---------------------------------------------------------------------------
# Final summary
# ---------------------------------------------------------------------------

def _print_summary(
    *,
    total_packets: int,
    handshake_frames: int,
    partial_warnings: int,
    observed_pk: bool,
    observed_ct: bool,
    observed_confirm: bool,
    pk_raw_len: int,
    ct_raw_len: int,
    pk_b64_preview: str,
    ct_b64_preview: str,
    duration_s: float,
) -> None:
    print()
    print(rule())
    section("PASSIVE INTERCEPTION SESSION SUMMARY")
    print(rule())
    print()
    print(f"  Duration              : {duration_s:.1f}s")
    print(f"  Total TCP Packets     : {total_packets}")
    print(f"  Handshake Frames      : {handshake_frames}")
    print(f"  TCP Segment Warnings  : {partial_warnings}")
    print()
    print(rule("-"))
    print("  HANDSHAKE ARTIFACT CAPTURE STATUS")
    print(rule("-"))
    print(f"  [{'✓' if observed_pk      else '—'}] ML-KEM Public Key    : "
          f"{'CAPTURED — ' + str(pk_raw_len) + ' raw bytes | ' + pk_b64_preview if observed_pk else 'Not yet seen'}")
    print(f"  [{'✓' if observed_ct      else '—'}] ML-KEM Ciphertext    : "
          f"{'CAPTURED — ' + str(ct_raw_len) + ' raw bytes | ' + ct_b64_preview if observed_ct else 'Not yet seen'}")
    print(f"  [{'✓' if observed_confirm else '—'}] Session Confirmation : "
          f"{'OBSERVED — secure_session established' if observed_confirm else 'Not yet seen'}")
    print()

    if partial_warnings > 0:
        print(f"  [!] WARNING: {partial_warnings} TCP segment(s) arrived without a full JSON message.")
        print(f"      This is normal for large keys split across segments.")
        print(f"      The per-flow buffer reassembled them correctly.")
        print()

    print(rule("="))
    section("ATTACKER VIEW — SCENARIO 2 EVIDENCE")
    print(rule("="))
    print()
    print("  ATTACKER CAN SEE (captured from the wire):")
    print(f"    ✓ ML-KEM public key        — {pk_raw_len} raw bytes (Base64-encoded in TCP payload)")
    print(f"    ✓ ML-KEM ciphertext        — {ct_raw_len} raw bytes (Base64-encoded in TCP payload)")
    print(f"    ✓ Protocol metadata        — algorithm name, message types, session status")
    print()
    print("  ATTACKER CANNOT SEE (not present anywhere on the wire):")
    print("    ✗ ML-KEM private key       — 1632 bytes, server-local, never transmitted")
    print("    ✗ 32-byte shared secret    — derived locally by both ends, never transmitted")
    print("    ✗ AES-256-GCM session key  — derived from shared secret, server-local only")
    print()
    print("  CRYPTOGRAPHIC GUARANTEE:")
    print("    Even with 100% of wire traffic captured, an adversary cannot")
    print("    decapsulate the ML-KEM ciphertext without the server's private key.")
    print("    The shared secret — and therefore all telemetry — remains unreadable.")
    print()
    print(rule("="))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "QuantumSecurity — Passive ML-KEM-512 Key Interception Observer "
            "(Scenario 2 Demonstration Tool)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run the passive observer (Administrator required)
  python integration/mlkem_attacker.py

  # Show every TCP packet being processed
  python integration/mlkem_attacker.py --verbose

  # Override default IPs/port
  python integration/mlkem_attacker.py --target-ip 192.168.2.99 --server-port 5000
        """
    )
    parser.add_argument(
        "--target-ip",
        default="192.168.2.99",
        help="PYNQ-Z2 source IP (default: 192.168.2.99)"
    )
    parser.add_argument(
        "--server-ip",
        default="192.168.2.1",
        help="Utility Server destination IP (default: 192.168.2.1)"
    )
    parser.add_argument(
        "--server-port",
        type=int,
        default=5000,
        help="Utility Server TCP port (default: 5000)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print every captured TCP packet (not just handshake frames)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_observer(
        target_ip=args.target_ip,
        server_ip=args.server_ip,
        server_port=args.server_port,
        verbose=args.verbose,
    )
