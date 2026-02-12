import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from app.config import get_settings
from app.database import get_all_user_emails

logger = logging.getLogger(__name__)


async def send_report_email(html_content: str) -> bool:
    settings = get_settings()
    if not all([settings.smtp_user, settings.smtp_password]):
        logger.warning("SMTP not configured, skipping")
        return False

    # 合并 .env 配置的收件人 + 数据库中用户邮箱（去重）
    recipients = set()
    if settings.email_to:
        for e in settings.email_to.split(","):
            if e.strip():
                recipients.add(e.strip())
    user_emails = await get_all_user_emails()
    recipients.update(user_emails)

    if not recipients:
        logger.warning("No recipients, skipping")
        return False

    recipients = list(recipients)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"\U0001f525 GitHub Trending \u65e5\u62a5 \u2014 {date.today()}"
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
