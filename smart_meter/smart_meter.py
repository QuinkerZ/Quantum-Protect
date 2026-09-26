import time
import json
import socket
import base64
import os
import sys
from pathlib import Path


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SMART_METER_DIR = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(SMART_METER_DIR) not in sys.path:
    sys.path.insert(0, str(SMART_METER_DIR))


from smart_meter.data_generator import EnergyDataGenerator

from crypto.mlkem import encapsulate
from crypto.secure_data import encrypt_data

# Physical FPGA HRR interface
from fpga_interface.fpga_interface import hardware_hrr


# ---------------------------------------------------------
# Utility Server connection
#
# Laptop testing:
#     SERVER_HOST defaults to 127.0.0.1
#
# PYNQ-Z2 testing:
#     Set SERVER_HOST to the laptop's IP address.
#
# Example:
#     export SERVER_HOST=192.168.2.1
# ---------------------------------------------------------
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))


# ---------------------------------------------------------
# FPGA configuration
#
# QUANTUM_FPGA=1 enables the physical PYNQ HRR test.
# On Windows keep it disabled.
# ---------------------------------------------------------
QUANTUM_FPGA = os.getenv(
    "QUANTUM_FPGA", "0"
).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def verify_fpga():
    """
    Verify the physical HRR accelerator on the PYNQ-Z2.

    This performs:
        A = 7
        B = 9
        result = (7 * 9) mod 3329

    Expected result:
        63
    """

    if not QUANTUM_FPGA:
        print("FPGA HRR backend disabled.")
        print("Using software-only startup.")
        return

    print("\n===== FPGA HRR SELF-TEST =====")
    print("Loading physical HRR accelerator...")

    result = hardware_hrr(7, 9)
    expected = 63

    print(f"HRR hardware result : {result}")
    print(f"Expected result     : {expected}")

    if result != expected:
        raise RuntimeError(
            f"FPGA HRR self-test failed: "
            f"got {result}, expected {expected}"
        )

    print("FPGA HRR self-test: PASS")


def receive_message(meter_socket, buffer):
    """Receive one newline-delimited JSON message."""

    while "\n" not in buffer:

        data = meter_socket.recv(4096)

        if not data:
            raise ConnectionError(
                "Utility Server disconnected."
            )

        buffer += data.decode("utf-8")

    message, buffer = buffer.split("\n", 1)

    return json.loads(message), buffer


def perform_mlkem_handshake(meter_socket, buffer):
    """Perform ML-KEM-512 key establishment."""

    print("\n===== ML-KEM-512 HANDSHAKE =====")

    # -----------------------------------------
    # 1. Receive server public key
    # -----------------------------------------
    message, buffer = receive_message(
        meter_socket,
        buffer
    )

    if message.get("type") != "mlkem_public_key":

        raise ValueError(
            "Expected ML-KEM public key from server."
        )

    encoded_public_key = message["public_key"]

    public_key = base64.b64decode(
        encoded_public_key
    )

    print(
        "Public key received from Utility Server."
    )

    # -----------------------------------------
    # 2. ML-KEM encapsulation
    # -----------------------------------------
    print(
        "Performing ML-KEM encapsulation..."
    )

    ciphertext, shared_secret = encapsulate(
        public_key
    )

    print("Ciphertext generated.")

    print(
        f"Shared secret size: "
        f"{len(shared_secret)} bytes"
    )

    # -----------------------------------------
    # 3. Send ciphertext to server
    # -----------------------------------------
    response = {
        "type": "mlkem_ciphertext",
        "algorithm": "ML-KEM-512",
        "ciphertext":
            base64.b64encode(
                ciphertext
            ).decode("ascii")
    }

    meter_socket.sendall(
        (json.dumps(response) + "\n")
        .encode("utf-8")
    )

    print(
        "Ciphertext sent to Utility Server."
    )

    # -----------------------------------------
    # 4. Receive server confirmation
    # -----------------------------------------
    confirmation, buffer = receive_message(
        meter_socket,
        buffer
    )

    if confirmation.get("type") != "secure_session":

        raise ValueError(
            "Invalid secure-session confirmation."
        )

    if confirmation.get("status") != "established":

        raise ValueError(
            "Secure session was not established."
        )

    print(
        "Utility Server confirmed secure session."
    )

    print(
        "ML-KEM handshake successful!"
    )

    return shared_secret, buffer


def run_smart_meter():

    # -----------------------------------------
    # FPGA verification
    # -----------------------------------------
    verify_fpga()

    # -----------------------------------------
    # Smart Meter generator
    # -----------------------------------------
    generator = EnergyDataGenerator()

    # -----------------------------------------
    # TCP socket
    # -----------------------------------------
    meter_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    print(
        f"Connecting to Utility Server at "
        f"{SERVER_HOST}:{SERVER_PORT}..."
    )

    meter_socket.connect(
        (SERVER_HOST, SERVER_PORT)
    )

    print(
        "Connected to Utility Server."
    )

    # Persistent TCP buffer
    buffer = ""

    try:

        # -----------------------------------------
        # ML-KEM secure session
        # -----------------------------------------
        shared_secret, buffer = (
            perform_mlkem_handshake(
                meter_socket,
                buffer
            )
        )

        print(
            f"\nSecure session ready. "
            f"Shared secret: "
            f"{len(shared_secret)} bytes"
        )

        # -----------------------------------------
        # Encrypted telemetry
        # -----------------------------------------
        print(
            "\nSending encrypted readings "
            "every 3 seconds..."
        )

        print(
            "Press Ctrl+C to stop.\n"
        )

        while True:

            # -----------------------------------------
            # Generate smart-meter reading
            # -----------------------------------------
            reading = (
                generator.generate_reading()
            )

            # -----------------------------------------
            # Encrypt reading
            # -----------------------------------------
            encrypted_data = encrypt_data(
                shared_secret,
                reading,
                "json"
            )

            # -----------------------------------------
            # Base64 for JSON transport
            # -----------------------------------------
            encoded_data = (
                base64.b64encode(
                    encrypted_data
                ).decode("ascii")
            )

            # -----------------------------------------
            # Create encrypted telemetry message
            # -----------------------------------------
            message = {
                "type": "encrypted_telemetry",
                "algorithm": "AES-256-GCM",
                "data": encoded_data
            }

            # -----------------------------------------
            # Send encrypted telemetry
            # -----------------------------------------
            meter_socket.sendall(
                (json.dumps(message) + "\n")
                .encode("utf-8")
            )

            print(
                "Encrypted telemetry sent."
            )

            print(
                f"Meter ID : "
                f"{reading['meter_id']}"
            )

            print(
                f"Power    : "
                f"{reading['power']} W"
            )

            print()

            time.sleep(3)

    except KeyboardInterrupt:

        print(
            "\nSmart Meter Stopped."
        )

    finally:

        meter_socket.close()


if __name__ == "__main__":
    run_smart_meter()