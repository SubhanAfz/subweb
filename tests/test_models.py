"""Tests covering the User model."""

from models import User


def test_password_hashing_roundtrip():
    """set_password stores a hash and check_password validates it."""
    user = User(username="tester", role=0)
    user.set_password("super-secret")

    assert user.password != "super-secret"
    assert user.check_password("super-secret")
    assert not user.check_password("wrong")
