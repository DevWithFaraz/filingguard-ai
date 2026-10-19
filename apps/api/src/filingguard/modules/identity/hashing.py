"""Hashed local secrets. Never persist or log the secret itself."""

import hashlib
import hmac
import secrets

PBKDF2_ITERATIONS = 210_000
_SCHEME = "pbkdf2_sha256"


def hash_secret(secret: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt, PBKDF2_ITERATIONS)
    return f"{_SCHEME}${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_secret(secret: str, stored: str) -> bool:
    try:
        scheme, iteration_text, salt_hex, digest_hex = stored.split("$", 3)
        if scheme != _SCHEME:
            return False
        iterations = int(iteration_text)
        if iterations < 100_000 or iterations > 1_000_000:
            return False
        expected = bytes.fromhex(digest_hex)
        computed = hashlib.pbkdf2_hmac(
            "sha256", secret.encode(), bytes.fromhex(salt_hex), iterations
        )
        return hmac.compare_digest(computed, expected)
    except (ValueError, TypeError):
        return False


DUMMY_SECRET_HASH = hash_secret("filingguard-dummy-local-identity-secret")
