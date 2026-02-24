import pytest
from unittest.mock import patch, MagicMock
from email_service import EmailService


class TestEmailService:
    def test_is_configured_false(self):
        service = EmailService()
        service.sender_email = ""
        service.sender_password = ""
        assert service.is_configured() is False
    
    def test_is_configured_true(self):
        service = EmailService()
        service.sender_email = "test@test.com"
        service.sender_password = "password"
        assert service.is_configured() is True
    
    @patch("email_service.smtplib.SMTP_SSL")
    def test_send_email_success(self, mock_smtp):
        service = EmailService()
        service.sender_email = "test@test.com"
        service.sender_password = "password"
        
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = service.send_email(
            to_email="recipient@test.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        assert result is True
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()
