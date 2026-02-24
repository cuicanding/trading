import pytest
from auth import AuthState


class TestAuthState:
    def test_validate_email_valid(self):
        state = AuthState()
        is_valid, error = state.validate_email("test@test.com")
        assert is_valid is True
        assert error == ""
    
    def test_validate_email_empty(self):
        state = AuthState()
        is_valid, error = state.validate_email("")
        assert is_valid is False
        assert "空" in error
    
    def test_validate_email_invalid_format(self):
        state = AuthState()
        is_valid, error = state.validate_email("invalid-email")
        assert is_valid is False
        assert "格式" in error
    
    def test_validate_username_valid(self):
        state = AuthState()
        is_valid, error = state.validate_username("testuser")
        assert is_valid is True
        assert error == ""
    
    def test_validate_username_too_short(self):
        state = AuthState()
        is_valid, error = state.validate_username("ab")
        assert is_valid is False
        assert "3-20" in error
    
    def test_validate_password_valid(self):
        state = AuthState()
        is_valid, error = state.validate_password("password123")
        assert is_valid is True
        assert error == ""
    
    def test_validate_password_too_short(self):
        state = AuthState()
        is_valid, error = state.validate_password("pass12")
        assert is_valid is False
        assert "8" in error
    
    def test_validate_password_no_digit(self):
        state = AuthState()
        is_valid, error = state.validate_password("password")
        assert is_valid is False
        assert "数字" in error
