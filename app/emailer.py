import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from app.config import get_settings
from app.database import get_all_user_emails

logger = logging.getLogger(__name__)


def _send_smtp(recipients: list[str], html_content: str) -> bool:
    """通过 SMTP 发送 HTML 邮件给指定收件人列表"""
    settings = get_settings()
    if not all([settings.smtp_user, settings.smtp_password]):
        logger.warning("SMTP not configured, skipping")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"\U0001f525 GitHub Trending 日报 — {date.today()}"
    msg["From"] = settings.smtp_user
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    for attempt in range(3):
        try:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_user, recipients, msg.as_string())
            logger.info(f"Email sent to {recipients}")
            return True
        except Exception as e:
            logger.error(f"Email attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                raise
    return False


async def send_email_to_user(html_content: str, email_addresses: list[str]) -> bool:
    """向单个用户的邮箱地址列表发送个性化报告"""
    if not email_addresses:
        return False
    return _send_smtp(email_addresses, html_content)


async def send_report_email(html_content: str) -> bool:
    """向 .env 配置的收件人发送报告（兜底，用于未注册用户）"""
    settings = get_settings()
    recipients = set()
    if settings.email_to:
        for e in settings.email_to.split(","):
            if e.strip():
                recipients.add(e.strip())

    if not recipients:
        return False

    return _send_smtp(list(recipients), html_content)
