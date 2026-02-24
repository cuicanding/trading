import pytest
from datetime import datetime, timedelta
from models import User, PasswordResetToken


class TestUser:
    def test_hash_password(self):
        password = "testpassword123"
        hashed = User.hash_password(password)
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        password = "testpassword123"
        user = User(id="test-id", password_hash=User.hash_password(password))
        assert user.verify_password(password) is True
    
    def test_verify_password_incorrect(self):
        password = "testpassword123"
        user = User(id="test-id", password_hash=User.hash_password(password))
        assert user.verify_password("wrongpassword") is False
    
    def test_to_dict(self):
        user = User(id="test-id", email="test@test.com", username="testuser")
        d = user.to_dict()
        assert d["id"] == "test-id"
        assert d["email"] == "test@test.com"
        assert d["username"] == "testuser"


class TestPasswordResetToken:
    def test_is_expired_false(self):
        token = PasswordResetToken(
            id="test-id",
            user_id="user-id",
            token="test-token",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        assert token.is_expired() is False
    
    def test_is_expired_true(self):
        token = PasswordResetToken(
            id="test-id",
            user_id="user-id",
            token="test-token",
            expires_at=datetime.now() - timedelta(hours=1)
        )
        assert token.is_expired() is True
