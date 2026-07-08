import hashlib
import hmac


def sign_payload(secret: str, body: bytes) -> str:
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={signature}"


def verify_signature(secret: str, body: bytes, signature: str) -> bool:
    expected = sign_payload(secret, body)
    return hmac.compare_digest(expected, signature)
