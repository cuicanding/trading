import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.qq.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465") or "465")
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "")
    SENDER_PASSWORD: str = os.getenv("SENDER_PASSWORD", "")
    APP_NAME: str = "AI Quant Trading"
    APP_URL: str = os.getenv("APP_URL", "http://localhost:3000")
