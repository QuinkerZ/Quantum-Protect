import socket
import json
import base64
import os
import sys
from pathlib import Path

# Add project root so we can import the crypto package
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from crypto.mlkem import (
    generate_keys,
    decapsulate
)

from crypto.secure_data import decrypt_data
from cryptography.exceptions import InvalidTag


# Utility Server network settings
# 0.0.0.0 allows the laptop to accept connections
# from the PYNQ-Z2 over Ethernet.
HOST = os.getenv("SERVER_HOST", "0.0.0.0")
PORT = int(os.getenv("SERVER_PORT", "5000"))

READINGS_FILE = Path(__file__).parent / "readings.json"


def validate_reading(reading):

    required_fields = [
        "meter_id",
        "timestamp",
        "voltage",
        "current",
        "power",
        "energy_kwh",
        "status"
    ]

    for field in required_fields:
        if field not in reading:
            return False

    if reading["voltage"] <= 0:
        return False

    if reading["current"] < 0:
        return False

    if reading["power"] < 0:
        return False

    if reading["energy_kwh"] < 0:
        return False

    return True


def save_reading(reading):

    try:
        with open(READINGS_FILE, "r") as file:
            readings = json.load(file)

    except (FileNotFoundError, json.JSONDecodeError):
        readings = []

    readings.append(reading)

    with open(READINGS_FILE, "w") as file:
        json.dump(
            readings,
            file,
            indent=4
        )


def calculate_statistics():

    try:
        with open(READINGS_FILE, "r") as file:
            readings = json.load(file)

    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    if not readings:
        return {}

    power_values = [
        reading["power"]
        for reading in readings
    ]

    statistics = {

        "number_of_readings":
            len(readings),

        "current_power":
            readings[-1]["power"],

        "average_power":
            round(
                sum(power_values) /
                len(power_values),
                2
            ),

        "maximum_power":
            max(power_values),

        "total_energy_kwh":
            readings[-1]["energy_kwh"],

        "meter_status":
            readings[-1]["status"]
    }

    return statistics


def receive_message(connection, buffer):
    """Receive one newline-delimited JSON message."""

    while "\n" not in buffer:

        data = connection.recv(4096)

        if not data:
            raise ConnectionError(
                "Smart Meter disconnected."
            )

        buffer += data.decode("utf-8")

    message, buffer = buffer.split("\n", 1)

    return json.loads(message), buffer


def perform_mlkem_handshake(
    connection,
    public_key,
    secret_key,
    buffer
):

    print("\n===== ML-KEM-512 HANDSHAKE =====")

    # -----------------------------------------
    # 1. Send server public key
    # -----------------------------------------

    message = {
        "type": "mlkem_public_key",
        "algorithm": "ML-KEM-512",
        "public_key":
            base64.b64encode(
                public_key
            ).decode("ascii")
    }

    connection.sendall(
        (json.dumps(message) + "\n")
        .encode("utf-8")
    )

    print(
        "ML-KEM public key sent to Smart Meter."
    )

    # -----------------------------------------
    # 2. Receive ciphertext
    # -----------------------------------------

    response, buffer = receive_message(
        connection,
        buffer
    )

    if response.get("type") != "mlkem_ciphertext":

        raise ValueError(
            "Expected ML-KEM ciphertext from Smart Meter."
        )

    encoded_ciphertext = response["ciphertext"]

    ciphertext = base64.b64decode(
        encoded_ciphertext
    )

    print("ML-KEM ciphertext received.")

    # -----------------------------------------
    # 3. Decapsulation
    # -----------------------------------------

    shared_secret = decapsulate(
        secret_key,
        ciphertext
    )

    print(
        "ML-KEM decapsulation successful."
    )

    print(
        f"Shared secret size: "
        f"{len(shared_secret)} bytes"
    )

    # -----------------------------------------
    # 4. Send confirmation
    # -----------------------------------------

    confirmation = {
        "type": "secure_session",
        "status": "established",
        "algorithm": "ML-KEM-512"
    }

    connection.sendall(
        (json.dumps(confirmation) + "\n")
        .encode("utf-8")
    )

    print("Secure session established.")

    # -----------------------------------------
    # 5. Record wire handshake artifacts
    # -----------------------------------------
    try:
        from datetime import datetime
        session_data = {
            "session_established_at": datetime.now().isoformat(),
            "algorithm": "ML-KEM-512",
            "pqc_standard": "NIST FIPS 203",
            "server_host": HOST,
            "server_port": PORT,
            "wire_artifacts": {
                "server_public_key_message": message,
                "public_key_b64": message["public_key"],
                "public_key_bytes_len": len(public_key),
                "meter_ciphertext_message": response,
                "ciphertext_b64": encoded_ciphertext,
                "ciphertext_bytes_len": len(ciphertext),
                "confirmation_message": confirmation,
            },
            "security_specs": {
                "public_key_size_bytes": len(public_key),
                "ciphertext_size_bytes": len(ciphertext),
                "shared_secret_size_bytes": len(shared_secret),
                "secret_key_size_bytes": len(secret_key),
            }
        }
        handshake_file = Path(__file__).parent / "mlkem_handshake_session.json"
        with open(handshake_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=4)
    except Exception:
        pass

    return shared_secret, buffer


def start_server():

    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server_socket.bind(
        (HOST, PORT)
    )

    server_socket.listen(1)

    print("Utility Server Started")

    print(
        f"Listening on {HOST}:{PORT}"
    )

    print(
        "Waiting for Smart Meter...\n"
    )

    connection, address = (
        server_socket.accept()
    )

    print(
        f"Smart Meter connected from {address}\n"
    )

    try:

        # -----------------------------------------
        # Persistent TCP buffer
        # -----------------------------------------

        buffer = ""

        # -----------------------------------------
        # Generate ML-KEM server keys
        # -----------------------------------------

        print(
            "Generating ML-KEM-512 key pair..."
        )

        public_key, secret_key = (
            generate_keys()
        )

        print("ML-KEM key pair generated.")

        print(
            "Server secret key remains private."
        )

        # -----------------------------------------
        # Secure session establishment
        # -----------------------------------------

        shared_secret, buffer = (
            perform_mlkem_handshake(
                connection,
                public_key,
                secret_key,
                buffer
            )
        )

        print(
            f"\nShared secret established: "
            f"{len(shared_secret)} bytes"
        )

        # -----------------------------------------
        # Encrypted telemetry processing
        # -----------------------------------------

        print(
            "\n===== SECURE TELEMETRY CHANNEL ====="
        )

        # IMPORTANT:
        # Do NOT reset buffer here.
        # It may already contain part of the
        # next message received during handshake.

        while True:

            # If we already have a complete message
            # in the buffer, process it first.
            if "\n" not in buffer:

                data = connection.recv(4096)

                if not data:

                    print(
                        "Smart Meter disconnected."
                    )

                    break

                print(
                    "Encrypted data received from "
                    "Smart Meter!"
                )

                buffer += data.decode("utf-8")

            while "\n" in buffer:

                message, buffer = (
                    buffer.split("\n", 1)
                )

                if not message.strip():
                    continue

                print(
                    "Raw encrypted message:"
                )

                print(message)

                received_message = json.loads(
                    message
                )

                # -----------------------------------------
                # Check message type
                # -----------------------------------------

                if received_message.get("type") != "encrypted_telemetry":

                    print(
                        "Unknown message type. "
                        "Ignoring.\n"
                    )

                    continue

                # -----------------------------------------
                # Decode Base64
                # -----------------------------------------

                encoded_data = (
                    received_message["data"]
                )

                encrypted_data = (
                    base64.b64decode(
                        encoded_data
                    )
                )

                # -----------------------------------------
                # Decrypt telemetry
                # -----------------------------------------

                try:
                    reading = decrypt_data(
                        shared_secret,
                        encrypted_data,
                        "json"
                    )
                except InvalidTag:
                    print(
                        "\n[SECURITY ALERT] AES-256-GCM AUTHENTICATION FAILED\n"
                        "[REJECTED] Tampered telemetry packet discarded\n"
                        "[SAFE] Reading NOT written to readings.json\n"
                    )
                    continue

                print(
                    "\nDecrypted Smart Meter Reading:"
                )

                print(reading)

                # -----------------------------------------
                # Validate and save
                # -----------------------------------------

                if validate_reading(reading):

                    save_reading(
                        reading
                    )

                    print(
                        "Reading is valid."
                    )

                    print(
                        "Reading saved "
                        "to readings.json\n"
                    )

                else:

                    print(
                        "Invalid reading. "
                        "Not saved.\n"
                    )

    except Exception as error:

        print("\nSERVER ERROR:")

        print(error)

    finally:

        connection.close()

        server_socket.close()

        print(
            "\nUtility Server Stopped."
        )

    # -----------------------------------------
    # Statistics
    # -----------------------------------------

    statistics = (
        calculate_statistics()
    )

    if statistics:

        print(
            "\n===== ENERGY STATISTICS ====="
        )

        print(
            f"Number of readings : "
            f"{statistics['number_of_readings']}"
        )

        print(
            f"Current power      : "
            f"{statistics['current_power']} W"
        )

        print(
            f"Average power      : "
            f"{statistics['average_power']} W"
        )

        print(
            f"Maximum power      : "
            f"{statistics['maximum_power']} W"
        )

        print(
            f"Total energy       : "
            f"{statistics['total_energy_kwh']} kWh"
        )

        print(
            f"Meter status       : "
            f"{statistics['meter_status']}"
        )


if __name__ == "__main__":

    start_server()