import json
import os
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# AES-256 requires a 32-byte key.
AES_KEY_SIZE = 32

# AES-GCM standard nonce size.
NONCE_SIZE = 12

# Used to identify this application's key derivation context.
HKDF_INFO = b"ML-KEM-SMART-METER-AES-256-GCM"


def derive_aes_key(shared_secret: bytes) -> bytes:
    """
    Derive a 256-bit AES key from the ML-KEM shared secret.
    """

    if not isinstance(shared_secret, bytes):
        raise TypeError("shared_secret must be bytes")

    if len(shared_secret) == 0:
        raise ValueError("shared_secret cannot be empty")

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=AES_KEY_SIZE,
        salt=None,
        info=HKDF_INFO,
    )

    return hkdf.derive(shared_secret)


def _serialize_data(data: Any) -> bytes:
    """
    Convert supported data types into bytes.

    Supported:
        bytes
        str
        JSON-compatible objects such as dict/list
    """

    if isinstance(data, bytes):
        return data

    if isinstance(data, str):
        return data.encode("utf-8")

    return json.dumps(
        data,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _deserialize_data(data: bytes, data_type: str) -> Any:
    """
    Convert decrypted bytes back to the requested data type.
    """

    if data_type == "bytes":
        return data

    if data_type == "string":
        return data.decode("utf-8")

    if data_type == "json":
        return json.loads(data.decode("utf-8"))

    raise ValueError(f"Unsupported data type: {data_type}")


def encrypt_data(
    shared_secret: bytes,
    data: Any,
    data_type: str = "json",
) -> bytes:
    """
    Encrypt data using an AES-256-GCM key derived from
    the ML-KEM shared secret.

    Returns:
        nonce + ciphertext + authentication tag
    """

    aes_key = derive_aes_key(shared_secret)

    plaintext = _serialize_data(data)

    nonce = os.urandom(NONCE_SIZE)

    aesgcm = AESGCM(aes_key)

    ciphertext = aesgcm.encrypt(
        nonce,
        plaintext,
        None,
    )

    # Store nonce together with ciphertext.
    return nonce + ciphertext


def decrypt_data(
    shared_secret: bytes,
    encrypted_data: bytes,
    data_type: str = "json",
) -> Any:
    """
    Decrypt AES-256-GCM encrypted data using a key derived
    from the ML-KEM shared secret.
    """

    if not isinstance(encrypted_data, bytes):
        raise TypeError("encrypted_data must be bytes")

    if len(encrypted_data) <= NONCE_SIZE:
        raise ValueError("encrypted_data is invalid or too short")

    aes_key = derive_aes_key(shared_secret)

    nonce = encrypted_data[:NONCE_SIZE]
    ciphertext = encrypted_data[NONCE_SIZE:]

    aesgcm = AESGCM(aes_key)

    plaintext = aesgcm.decrypt(
        nonce,
        ciphertext,
        None,
    )

    return _deserialize_data(plaintext, data_type)