from utils.password_utils import hash_password, verify_password


def test_hash_is_not_plain():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"


def test_verify_correct_password():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_wrong_password():
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False


def test_same_password_different_hashes():
    h1 = hash_password("mypassword")
    h2 = hash_password("mypassword")
    assert h1 != h2  # bcrypt использует соль
