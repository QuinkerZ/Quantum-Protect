from crypto.mlkem import generate_keys, encapsulate, decapsulate


def test_basic_exchange():
    """Test one complete meter-server exchange."""

    public_key, secret_key = generate_keys()

    ciphertext, meter_secret = encapsulate(public_key)

    server_secret = decapsulate(
        secret_key,
        ciphertext
    )

    assert meter_secret == server_secret

    print("Basic exchange: PASS")


def test_repeated_exchanges():
    """
    Test multiple encapsulation/decapsulation operations
    using the same server key pair.
    """

    public_key, secret_key = generate_keys()

    for i in range(100):

        ciphertext, meter_secret = encapsulate(public_key)

        server_secret = decapsulate(
            secret_key,
            ciphertext
        )

        assert meter_secret == server_secret

    print("100 repeated exchanges: PASS")


def test_different_shared_secrets():
    """
    Verify that separate encapsulations generate
    different shared secrets.
    """

    public_key, _ = generate_keys()

    _, secret_1 = encapsulate(public_key)
    _, secret_2 = encapsulate(public_key)

    assert secret_1 != secret_2

    print("Independent shared secrets: PASS")


def test_empty_public_key():
    """Test invalid public-key handling."""

    try:
        encapsulate(b"")
        assert False, "Expected ValueError"

    except ValueError:
        print("Empty public key handling: PASS")


def test_empty_secret_key():
    """Test invalid secret-key handling."""

    try:
        decapsulate(b"", b"some ciphertext")
        assert False, "Expected ValueError"

    except ValueError:
        print("Empty secret key handling: PASS")


def test_empty_ciphertext():
    """Test invalid ciphertext handling."""

    public_key, secret_key = generate_keys()

    try:
        decapsulate(secret_key, b"")
        assert False, "Expected ValueError"

    except ValueError:
        print("Empty ciphertext handling: PASS")


if __name__ == "__main__":

    print("=" * 50)
    print("ML-KEM-512 TEST SUITE")
    print("=" * 50)

    test_basic_exchange()
    test_repeated_exchanges()
    test_different_shared_secrets()
    test_empty_public_key()
    test_empty_secret_key()
    test_empty_ciphertext()

    print("=" * 50)
    print("ALL TESTS PASSED")
    print("=" * 50)