"""
VisionX — Password Hashing
==============================
Single source of truth for credential hashing.

Design notes
------------
1. **bcrypt is preferred**, with a stdlib ``scrypt`` fallback so that minimal /
   CI installs without a C extension still get a *real* password hash rather
   than silently degrading to plaintext.
2. Hashes are **self-describing** (``$scheme$...``) so both schemes can coexist
   in one database and be migrated lazily via :func:`needs_rehash`.
3. Passwords are **SHA-256 pre-hashed** before bcrypt. bcrypt silently truncates
   input at 72 bytes; pre-hashing removes that cliff and makes long passphrases
   behave correctly.

Why not passlib?
    ``passlib`` 1.7.4 (the last release) is incompatible with ``bcrypt`` >= 4.1
    and raises ``ValueError: password cannot be longer than 72 bytes`` for
    *any* input. It was declared in requirements.txt but never imported, so
    this module replaces it outright rather than pinning a broken combination.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets

from loguru import logger

try:
    import bcrypt as _bcrypt
except ImportError:  # pragma: no cover - exercised only on minimal installs
    _bcrypt = None  # type: ignore[assignment]


# --- Tuning -------------------------------------------------------------
# bcrypt cost 12 ~= 250ms on 2026 commodity hardware. Raise as hardware improves.
BCRYPT_ROUNDS = 12

# scrypt parameters per OWASP Password Storage Cheat Sheet (n=2^15, r=8, p=1).
SCRYPT_N = 2**15
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_SALT_BYTES = 16
SCRYPT_KEY_LEN = 32

PREFERRED_SCHEME = "bcrypt" if _bcrypt is not None else "scrypt"

if _bcrypt is None:
    logger.warning(
        "bcrypt unavailable — falling back to stdlib scrypt for password hashing. "
        "Install bcrypt for the preferred backend: pip install bcrypt"
    )


def _prehash(plain: str) -> bytes:
    """
    SHA-256 pre-hash, base64-encoded.

    Produces a fixed 44-byte value, which sidesteps bcrypt's 72-byte silent
    truncation while preserving full entropy of the original passphrase.
    """
    digest = hashlib.sha256(plain.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(plain: str) -> str:
    """
    Hash a plaintext password using the preferred available backend.

    Returns a self-describing hash string safe to store in a database.
    """
    if not plain:
        raise ValueError("Password must not be empty")

    if _bcrypt is not None:
        salt = _bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        digest = _bcrypt.hashpw(_prehash(plain), salt)
        return f"$bcrypt${digest.decode('ascii')}"

    salt = os.urandom(SCRYPT_SALT_BYTES)
    digest = hashlib.scrypt(
        _prehash(plain),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_KEY_LEN,
    )
    return (
        f"$scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}$"
        f"{base64.b64encode(salt).decode('ascii')}$"
        f"{base64.b64encode(digest).decode('ascii')}"
    )


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a stored hash.

    Returns False (never raises) for malformed or unknown-scheme hashes, so a
    corrupted database row cannot turn into a 500 on the login path.
    """
    if not plain or not hashed:
        return False

    try:
        if hashed.startswith("$bcrypt$"):
            if _bcrypt is None:
                logger.error("bcrypt hash encountered but bcrypt is not installed")
                return False
            return _bcrypt.checkpw(
                _prehash(plain), hashed[len("$bcrypt$"):].encode("ascii")
            )

        if hashed.startswith("$scrypt$"):
            _, _, n_s, r_s, p_s, salt_b64, digest_b64 = hashed.split("$")
            expected = hashlib.scrypt(
                _prehash(plain),
                salt=base64.b64decode(salt_b64),
                n=int(n_s),
                r=int(r_s),
                p=int(p_s),
                dklen=SCRYPT_KEY_LEN,
            )
            return hmac.compare_digest(expected, base64.b64decode(digest_b64))

    except Exception as e:  # noqa: BLE001 - never leak crypto errors to callers
        logger.warning(f"Password verification error: {type(e).__name__}")
        return False

    logger.warning("Unknown password hash scheme encountered")
    return False


def needs_rehash(hashed: str) -> bool:
    """
    Whether a stored hash should be upgraded on next successful login.

    True when the hash uses a non-preferred scheme or weaker-than-current cost.
    """
    if not hashed:
        return True

    if _bcrypt is not None:
        if not hashed.startswith("$bcrypt$"):
            return True
        try:
            # Our prefix wraps a native bcrypt hash: $bcrypt$ + $2b$<rounds>$<salt+digest>
            # Strip the prefix first, then read the cost field, rather than
            # indexing into the combined string (the doubled '$' shifts fields).
            native = hashed[len("$bcrypt$"):]
            return int(native.split("$")[2]) < BCRYPT_ROUNDS
        except (IndexError, ValueError):
            return True

    return not hashed.startswith("$scrypt$")


def generate_password(length: int = 20) -> str:
    """Generate a cryptographically secure random password (bootstrap/admin reset)."""
    return secrets.token_urlsafe(length)[:length]
