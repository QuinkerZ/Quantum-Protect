from crypto.mlkem import generate_keys, encapsulate, decapsulate


def main():

    print("=" * 50)
    print("ML-KEM-512 SMART METER KEY ESTABLISHMENT")
    print("=" * 50)

    # ==========================================
    # 1. UTILITY SERVER: Generate key pair
    # ==========================================

    print("\n[SERVER]")
    print("Generating ML-KEM key pair...")

    public_key, secret_key = generate_keys()

    print("Public key generated.")
    print("Secret key generated.")
    print("Secret key remains on the server.")


    # ==========================================
    # 2. SERVER -> SMART METER
    # ==========================================

    print("\n[SERVER -> METER]")
    print("Sending public key to smart meter...")

    meter_public_key = public_key

    print("Public key received by meter.")


    # ==========================================
    # 3. SMART METER: Encapsulation
    # ==========================================

    print("\n[METER]")
    print("Performing ML-KEM encapsulation...")

    ciphertext, meter_shared_secret = encapsulate(
        meter_public_key
    )

    print("Ciphertext generated.")
    print("Shared secret generated.")


    # ==========================================
    # 4. SMART METER -> SERVER
    # ==========================================

    print("\n[METER -> SERVER]")
    print("Sending ciphertext to utility server...")

    received_ciphertext = ciphertext

    print("Ciphertext received by server.")


    # ==========================================
    # 5. SERVER: Decapsulation
    # ==========================================

    print("\n[SERVER]")
    print("Performing ML-KEM decapsulation...")

    server_shared_secret = decapsulate(
        secret_key,
        received_ciphertext
    )

    print("Shared secret recovered.")


    # ==========================================
    # 6. VERIFY
    # ==========================================

    print("\n[VERIFICATION]")

    if meter_shared_secret == server_shared_secret:
        print("SUCCESS: Shared secrets match!")
    else:
        print("FAILURE: Shared secrets do not match!")


    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()