from __future__ import annotations

import hashlib
import hmac
import secrets

ITERATIONS = 260_000
ALGORITHM = "pbkdf2_sha256"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        ITERATIONS,
    )
    return f"{ALGORITHM}${ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored_value: str) -> bool:
    if not stored_value:
        return False

    if not stored_value.startswith(f"{ALGORITHM}$"):
        return hmac.compare_digest(password, stored_value)

    try:
        _, iterations, salt, expected = stored_value.split("$", 3)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
    except ValueError:
        return False

    return hmac.compare_digest(digest, expected)
