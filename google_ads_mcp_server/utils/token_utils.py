import secrets
import hashlib
import hmac


def generate_token(length: int = 32) -> str:
    """Generate a secure random token string."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Return the SHA-256 hash of the provided token."""
    if token is None:
        raise ValueError("token must not be None")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token(stored_hash: str, provided_token: str) -> bool:
    """Check whether the hash of the provided token matches the stored hash."""
    if stored_hash is None or provided_token is None:
        return False
    provided_hash = hash_token(provided_token)
    return hmac.compare_digest(stored_hash, provided_hash)
