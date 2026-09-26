"""
Golden software reference model for the HRR modular reduction block.

Fixed competition parameters:
    q       = 3329
    R       = 2^12 = 4096
    k       = 24
    mu      = floor(2^24 / q) = 5039
    q_prime = -q^(-1) mod R = 3327

For inputs 0 <= a,b < q, hrr(a,b) returns:

    r = (a * b) mod q

The implementation performs the HRR pipeline using Barrett conversion
and Montgomery reduction. The direct modulo operation is NOT used inside
the HRR calculation; it is reserved for the independent test oracle.
"""

Q = 3329
R = 1 << 12
K = 24
MU = (1 << K) // Q
Q_PRIME = 3327


def barrett_reduce(x: int) -> int:
    """Barrett reduction for the fixed modulus q."""
    if x < 0:
        raise ValueError("x must be non-negative")

    q_hat = (x * MU) >> K
    t = x - q_hat * Q

    if t >= Q:
        t -= Q

    if not 0 <= t < Q:
        raise ArithmeticError(f"Barrett result out of range: {t}")

    return t


def to_montgomery(x: int) -> int:
    """Convert x from the normal domain to the Montgomery domain."""
    if not 0 <= x < Q:
        raise ValueError(f"x must satisfy 0 <= x < {Q}")

    return barrett_reduce(x * R)


def montgomery_redc(T: int) -> int:
    """
    Montgomery REDC:

        m = (T * q_prime) mod R
        u = (T + m*q) / R
        if u >= q: u = u - q
    """
    if T < 0:
        raise ValueError("T must be non-negative")

    m = (T * Q_PRIME) & (R - 1)
    u = (T + m * Q) >> 12

    if u >= Q:
        u -= Q

    if not 0 <= u < Q:
        raise ArithmeticError(f"Montgomery result out of range: {u}")

    return u


def montgomery_multiply(a_bar: int, b_bar: int) -> int:
    """Multiply two Montgomery-domain operands."""
    if not 0 <= a_bar < Q:
        raise ValueError("a_bar must be in [0, q)")
    if not 0 <= b_bar < Q:
        raise ValueError("b_bar must be in [0, q)")

    T = a_bar * b_bar
    return montgomery_redc(T)


def from_montgomery(x_bar: int) -> int:
    """Convert a Montgomery-domain value back to the normal domain."""
    if not 0 <= x_bar < Q:
        raise ValueError("x_bar must be in [0, q)")

    return montgomery_redc(x_bar)


def hrr(a: int, b: int) -> int:
    """
    Complete HRR modular multiplication.

    Returns:
        r = (a * b) mod q

    for 0 <= a,b < q.
    """
    if not 0 <= a < Q:
        raise ValueError(f"a must satisfy 0 <= a < {Q}")
    if not 0 <= b < Q:
        raise ValueError(f"b must satisfy 0 <= b < {Q}")

    a_bar = to_montgomery(a)
    b_bar = to_montgomery(b)

    product_bar = montgomery_multiply(a_bar, b_bar)

    return from_montgomery(product_bar)
