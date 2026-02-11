import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from app.config import get_settings

logger = logging.getLogger(__name__)


async def send_report_email(html_content: str) -> bool:
    settings = get_settings()
    if not all([settings.smtp_user, settings.smtp_password, settings.email_to]):
        logger.warning("Email not configured, skipping")
        return False

    # 支持逗号分隔多个收件人
    recipients = [e.strip() for e in settings.email_to.split(",") if e.strip()]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔥 GitHub Trending 日报 — {date.today()}"
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
