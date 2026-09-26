# 🛡️ QuantumSecurity — 3-Scenario Live Demonstration & Presentation Plan

> **For Team & ChatGPT Coordination**  
> **Project:** QuantumSecurity: Post-Quantum Cryptographic (ML-KEM-512) & Hardware-Accelerated (FPGA) Smart Grid Telemetry  
> **Target Scope:** 3 Core Security Scenarios (Wire Confidentiality, Post-Quantum Key Isolation, MitM Packet Tampering)

---

## 1. Executive Summary & Objective
This live presentation demonstrates the post-quantum resilience and cryptographic integrity of the **QuantumSecurity Smart Meter Architecture** against three real-world cyberattack vectors:
1. **Scenario 1:** Passive Network Eavesdropping & Wire Sniffing (Confidentiality via AES-256-GCM)
2. **Scenario 2:** Post-Quantum Key Interception (ML-KEM-512 Lattice-Based Key Isolation)
3. **Scenario 3:** Active Man-in-the-Middle (MitM) Packet Tampering & Bit-Flipping (Integrity via `InvalidTag`)

All scenarios execute on the **real cryptographic implementation** (`pqcrypto` NIST FIPS 203 ML-KEM-512 and `cryptography` AES-256-GCM) with no mocked responses.

---

## 2. Team Role Division (3 Presenters)

| Role / Member | Focus Area | Primary Responsibility |
| :--- | :--- | :--- |
| **Member 1 (KEM & Architecture)** | **Scenario 2 Lead** | Explains the PYNQ-Z2 hardware setup, ML-KEM-512 post-quantum key exchange, public/private key sizes, and proves why recorded wire traffic cannot be decrypted. |
| **Member 2 (Telemetry & Confidentiality)** | **Scenario 1 Lead** | Explains live telemetry generation, AES-256-GCM encryption, wire packet capture, and demonstrates 0% plaintext leakage. |
| **Member 3 (Active MitM & Dashboard)** | **Scenario 3 Lead** | Simulates live active packet corruption (bit-flips and tag tampering), proves instant cryptographic rejection (`InvalidTag`), and links it with the live Streamlit Dashboard. |

---

## 3. High-Level Architecture & Threat Model

```
                       ┌──────────────────────────────────────────────────────────┐
                       │               PYNQ-Z2 Smart Meter (ARM Core)             │
                       │  • Generates Telemetry (V, I, W, kWh)                    │
                       │  • Encapsulates ML-KEM-512 Key ➔ 32B Shared Secret       │
                       │  • Encrypts Payload with AES-256-GCM                     │
                       └────────────────────────────┬─────────────────────────────┘
                                                    │
                                   Direct Ethernet (TCP/IP :5000)
                        ┌───────────────────────────┴────────────────────────────┐
                        │ ATTACK VECTORS TESTED:                                 │
                        │  [Scenario 1] Passive Wire Sniffing (Eavesdropping)    │
                        │  [Scenario 2] Public Key & Ciphertext Capture (KEM)    │
                        │  [Scenario 3] Active Bit-Flip & Tag Tampering (MitM)   │
                        └───────────────────────────┬────────────────────────────┘
                                                    │
                       ┌────────────────────────────▼─────────────────────────────┐
                       │         Windows Utility Server & Dashboard Host          │
                       │  • ML-KEM-512 Decapsulation ➔ Identical 32B Secret       │
                       │  • AES-256-GCM Authentication Tag Validation             │
                       │  • Live Dashboard Streamlit Cockpit (:8501)              │
                       └──────────────────────────────────────────────────────────┘
```

---

## 4. Scenario Breakdown & Presenter Scripts

---

### 📡 SCENARIO 1: Wire Eavesdropping & Telemetry Confidentiality
- **Presenter:** Member 2
- **Threat Model:** A passive eavesdropper sniffs TCP traffic on port `5000` to steal sensitive consumer electrical consumption data (voltage, current, active power, billing energy).
- **Defense Mechanism:** Every reading is encrypted using **AES-256-GCM** with a dynamic session key derived from ML-KEM-512.
- **Execution:** Select `[1]` in `integration/demo_security_scenarios.py`

#### What the Audience Sees & Presenter Talking Points:
1. **Plaintext Reading Generated:**
   ```
   Plaintext Reading: Meter=SM001, Voltage=228.45V, Power=1071.43W, Current=4.69A, Energy=0.000893kWh
   ```
   *Talking Point:* "In an unencrypted legacy grid, this raw telemetry travels in plaintext, exposing customer activity and power usage patterns."
2. **Encrypted Wire Message Transmitted:**
   ```json
   {"type": "encrypted_telemetry", "algorithm": "AES-256-GCM", "data": "v3rQOlJTGhIWsC5+65dz..."}
   ```
3. **Automated Leakage Audit:**
   The script scans the payload for sensitive tokens (`SM001`, `voltage`, `power`, `energy_kwh`, numbers).
   ```
   [CONFIRMED] Zero plaintext leakage: all sensitive fields are hidden.
   ```
4. **Authorized Utility Server Recovery:**
   Utility Server decrypts the payload and matches the original telemetry identically.
   ```
   >>> RESULT: SCENARIO 1 [PASS]
   ```

---

### 🔑 SCENARIO 2: Post-Quantum ML-KEM-512 Key Interception Resistance
- **Presenter:** Member 1
- **Threat Model:** A "Harvest Now, Decrypt Later" adversary records all network initialization packets—capturing both the Server's Public Key and the Meter's Encapsulated Ciphertext.
- **Defense Mechanism:** **NIST FIPS 203 (ML-KEM-512)** lattice-based cryptography. The 32-byte shared session secret is derived independently in memory and is **never transmitted over the wire**.
- **Execution:** Select `[2]` in `integration/demo_security_scenarios.py`

#### What the Audience Sees & Presenter Talking Points:
1. **Key Generation Parameters:**
   - **Public Key (Wire-visible):** 800 bytes
   - **Secret Key (Server private memory only):** 1,632 bytes
   - **Encapsulated Ciphertext (Wire-visible):** 768 bytes
   - **Derived Session Secret:** 32 bytes
2. **Adversary Interception Simulation:**
   The attacker intercepts both the 800-byte Public Key and the 768-byte Ciphertext.
3. **Cryptographic Key Isolation Proof:**
   The script verifies that the 32-byte shared secret does not appear inside any wire artifact.
   ```
   [CONFIRMED] Shared secret bytes do not appear in any wire artifact.
   ```
4. **Unauthorized Decryption Failure:**
   Demonstrates that attempting to decrypt telemetry with any unauthorized key immediately triggers an authentication error.
   ```
   [CONFIRMED] Adversary cannot decrypt telemetry using unauthorized secret key.
   ```
5. **Legitimate Decapsulation:**
   The server decapsulates using its private key and obtains the identical 32-byte secret.
   ```
   >>> RESULT: SCENARIO 2 [PASS]
   ```

---

### ⚡ SCENARIO 3: Active Man-in-the-Middle (MitM) Packet Tampering & Bit-Flipping
- **Presenter:** Member 3
- **Threat Model:** An active MitM attacker intercepts in-flight packets and modifies bytes (e.g., attempting to falsify power readings or spoof billing numbers).
- **Defense Mechanism:** **AES-256-GCM Galois Authenticated Encryption**. Any 1-bit change in either the ciphertext or the 16-byte authentication tag causes authentication tag verification to fail.
- **Execution:** Select `[3]` in `integration/demo_security_scenarios.py`

#### What the Audience Sees & Presenter Talking Points:
1. **Legitimate Payload Encrypted:**
   $12\text{B Nonce} + 142\text{B Ciphertext} + 16\text{B Auth Tag}$.
2. **Attack Vector A — Ciphertext Bit-Flip:**
   Adversary flips one byte in the ciphertext body.
   ```
   [CAUGHT] Ciphertext body tampering detected! Raised InvalidTag.
   ```
3. **Attack Vector B — Authentication Tag Modification:**
   Adversary attempts to forge or tweak the 16-byte tag.
   ```
   [CAUGHT] Authentication tag tampering detected! Raised InvalidTag.
   ```
4. **Attack Vector C — Packet Truncation:**
   Adversary injects incomplete malformed bytes.
   ```
   [CAUGHT] Truncated packet rejected! Raised ValueError.
   ```
5. **Dashboard Correlation:**
   Demonstrate that only 100% verified, authenticated packets reach `server/readings.json` and appear on the live dashboard.
   ```
   >>> RESULT: SCENARIO 3 [PASS]
   ```

---

## 5. Live Demonstration Commands

Run the demo CLI from the repository root:

```powershell
# Open terminal in project root
cd "C:\Users\toshi\Downloads\QuantumSecurity (tim)\QuantumSecurity"

# Run interactive presentation mode (pauses between steps with [Enter])
.\.venv\Scripts\python.exe integration/demo_security_scenarios.py
```

### Presentation Controls in Terminal:
- Press **`S`** ➔ Step-by-Step Interactive Walkthrough (Ideal for team presentation).
- Press **`1`** ➔ Run Scenario 1 only.
- Press **`2`** ➔ Run Scenario 2 only.
- Press **`3`** ➔ Run Scenario 3 only.
- Press **`A`** ➔ Run All 4 Scenarios Sequentially.

---

## 6. Presentation Checklist for Team

- [ ] **Member 1:** Ready with ML-KEM-512 explanation (800B Public Key, 1632B Secret Key, 768B Ciphertext, 32B Shared Secret).
- [ ] **Member 2:** Ready with Telemetry confidentiality explanation (AES-256-GCM, 0% plaintext wire leakage).
- [ ] **Member 3:** Ready with MitM bit-flip and `InvalidTag` explanation + live dashboard reference.
- [ ] **Terminal:** Verified command `.\.venv\Scripts\python.exe integration/demo_security_scenarios.py` runs cleanly.
