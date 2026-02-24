import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config import Config


class EmailService:
    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.sender_email = Config.SENDER_EMAIL
        self.sender_password = Config.SENDER_PASSWORD
    
    def is_configured(self) -> bool:
        return bool(self.sender_email and self.sender_password)
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        if not self.is_configured():
            print(f"[邮件未配置] 收件人: {to_email}, 主题: {subject}")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{Config.APP_NAME} <{self.sender_email}>"
            msg["To"] = to_email
            
            msg.attach(MIMEText(body, "plain", "utf-8"))
            
            if html_body:
                msg.attach(MIMEText(html_body, "html", "utf-8"))
            
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())
            
            return True
        except Exception as e:
            print(f"发送邮件失败: {str(e)}")
            return False
    
    def send_welcome_email(self, to_email: str, username: str) -> bool:
        subject = f"欢迎加入 {Config.APP_NAME}"
        body = f"""
您好 {username}，

欢迎加入 {Config.APP_NAME}！

您现在可以使用我们的量化交易平台进行股票分析和策略回测。

如有任何问题，请随时联系我们。

祝您投资顺利！
{Config.APP_NAME} 团队
"""
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #00f0ff;">欢迎加入 {Config.APP_NAME}</h2>
    <p>您好 <strong>{username}</strong>，</p>
    <p>欢迎加入 {Config.APP_NAME}！</p>
    <p>您现在可以使用我们的量化交易平台进行股票分析和策略回测。</p>
    <p>如有任何问题，请随时联系我们。</p>
    <p>祝您投资顺利！</p>
    <p style="color: #888;">{Config.APP_NAME} 团队</p>
</body>
</html>
"""
        return self.send_email(to_email, subject, body, html_body)
    
    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        reset_link = f"{Config.APP_URL}/reset-password/confirm?token={reset_token}"
        subject = f"重置您的密码 - {Config.APP_NAME}"
        body = f"""
您好，

您收到这封邮件是因为您请求重置密码。

请点击以下链接重置密码（链接1小时内有效）：
{reset_link}

如果您没有请求重置密码，请忽略此邮件。

{Config.APP_NAME} 团队
"""
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #00f0ff; margin-bottom: 20px;">重置您的密码</h2>
    <p style="margin-bottom: 10px;">您好，</p>
    <p style="margin-bottom: 20px;">您收到这封邮件是因为您请求重置密码。</p>
    <table role="presentation" cellspacing="0" cellpadding="0" style="margin-bottom: 20px;">
        <tr>
            <td style="background-color: #00f0ff; border-radius: 8px;">
                <a href="{reset_link}" style="display: inline-block; padding: 14px 24px; color: #0a0a0f; text-decoration: none; font-weight: 600; font-size: 16px;">点击重置密码</a>
            </td>
        </tr>
    </table>
    <p style="color: #888; margin-bottom: 10px;">链接1小时内有效</p>
    <p style="color: #888; font-size: 12px; margin-bottom: 20px;">如果您没有请求重置密码，请忽略此邮件。</p>
    <hr style="border: none; border-top: 1px solid #333; margin-bottom: 20px;">
    <p style="color: #888;">{Config.APP_NAME} 团队</p>
</body>
</html>
"""
        return self.send_email(to_email, subject, body, html_body)


email_service = EmailService()
