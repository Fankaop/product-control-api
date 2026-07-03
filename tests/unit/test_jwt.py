from unittest.mock import patch
from utils.jwt_utils import create_access_token, decode_access_token


def test_create_and_decode_token():
    token = create_access_token(user_id=42)
    decoded = decode_access_token(token)
    assert decoded == 42


def test_decode_invalid_token():
    result = decode_access_token("not.a.valid.token")
    assert result is None


def test_decode_expired_token():
    with patch("utils.jwt_utils.settings") as mock_settings:
        mock_settings.jwt_expire_minutes = -1
        mock_settings.jwt_secret_key = "test-secret"
        mock_settings.jwt_algorithm = "HS256"
        token = create_access_token(user_id=1)

    result = decode_access_token(token)
    assert result is None
