from pqcrypto.kem import ml_kem_512


ALGORITHM = "ML-KEM-512"


def generate_keys():
    """Generate an ML-KEM-512 key pair."""

    if hasattr(ml_kem_512, "keygen"):
        return ml_kem_512.keygen()

    return ml_kem_512.generate_keypair()


def encapsulate(public_key):
    """Encapsulate a shared secret."""

    if not public_key:
        raise ValueError("Public key cannot be empty.")

    if hasattr(ml_kem_512, "encaps"):
        return ml_kem_512.encaps(public_key)

    return ml_kem_512.encrypt(public_key)


def decapsulate(secret_key, ciphertext):
    """Decapsulate a shared secret."""

    if not secret_key:
        raise ValueError("Secret key cannot be empty.")

    if not ciphertext:
        raise ValueError("Ciphertext cannot be empty.")

    if hasattr(ml_kem_512, "decaps"):
        return ml_kem_512.decaps(secret_key, ciphertext)

    return ml_kem_512.decrypt(secret_key, ciphertext)