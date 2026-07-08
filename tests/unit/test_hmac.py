from utils.hmac_utils import sign_payload, verify_signature


def test_sign_payload_format():
    signature = sign_payload("secret", b"body")
    assert signature.startswith("sha256=")
    assert len(signature) > 10


def test_verify_signature_valid():
    body = b'{"event": "batch.closed"}'
    secret = "my-secret"
    signature = sign_payload(secret, body)
    assert verify_signature(secret, body, signature) is True


def test_verify_signature_wrong_secret():
    body = b'{"event": "batch.closed"}'
    signature = sign_payload("correct-secret", body)
    assert verify_signature("wrong-secret", body, signature) is False


def test_verify_signature_tampered_body():
    secret = "my-secret"
    signature = sign_payload(secret, b"original body")
    assert verify_signature(secret, b"tampered body", signature) is False


def test_sign_same_inputs_same_output():
    sig1 = sign_payload("secret", b"body")
    sig2 = sign_payload("secret", b"body")
    assert sig1 == sig2
