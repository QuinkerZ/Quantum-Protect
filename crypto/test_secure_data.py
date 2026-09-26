from crypto.secure_data import encrypt_data, decrypt_data


def test_json():
    shared_secret = b"test-shared-secret-for-aes-layer"

    original = {
        "meter_id": "M001",
        "energy_kwh": 12.45,
        "voltage": 230.2,
        "current": 4.7,
    }

    encrypted = encrypt_data(
        shared_secret,
        original,
        "json",
    )

    decrypted = decrypt_data(
        shared_secret,
        encrypted,
        "json",
    )

    assert original == decrypted

    print("JSON encryption/decryption: PASS")


def test_string():
    shared_secret = b"test-shared-secret-for-aes-layer"

    original = "Energy = 12.45 kWh"

    encrypted = encrypt_data(
        shared_secret,
        original,
        "string",
    )

    decrypted = decrypt_data(
        shared_secret,
        encrypted,
        "string",
    )

    assert original == decrypted

    print("String encryption/decryption: PASS")


def test_bytes():
    shared_secret = b"test-shared-secret-for-aes-layer"

    original = b"12.45,230.2,4.7"

    encrypted = encrypt_data(
        shared_secret,
        original,
        "bytes",
    )

    decrypted = decrypt_data(
        shared_secret,
        encrypted,
        "bytes",
    )

    assert original == decrypted

    print("Bytes encryption/decryption: PASS")


if __name__ == "__main__":
    print("=" * 50)
    print("SECURE DATA LAYER TEST")
    print("=" * 50)

    test_json()
    test_string()
    test_bytes()

    print("=" * 50)
    print("ALL TESTS PASSED")
    print("=" * 50)