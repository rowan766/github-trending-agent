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


async def send_verification_code(email: str, code: str) -> bool:
    """向指定邮箱发送 6 位数字验证码"""
    settings = get_settings()
    if not all([settings.smtp_user, settings.smtp_password]):
        logger.warning("SMTP not configured, cannot send verification code")
        return False

    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:24px">
      <p style="margin:0 0 16px;padding:12px 16px;background:#fff8f0;border:1px solid #f7c99d;border-radius:8px;font-size:14px;color:#8a4b08">
        线上访问地址：<a href="https://ai.zenoly.cn/web/#/login" style="color:#c65d09;font-weight:bold;text-decoration:none">https://ai.zenoly.cn/web/#/login</a>
      </p>
      <h2 style="color:#f0883e;margin-bottom:8px">🔥 GitHub Trending Agent</h2>
      <p style="color:#555;margin-bottom:20px">您正在绑定接收邮箱，验证码如下：</p>
      <div style="font-size:36px;font-weight:bold;color:#333;letter-spacing:12px;
                  background:#f5f7fa;border-radius:8px;padding:20px 24px;
                  text-align:center;margin-bottom:20px">{code}</div>
      <p style="color:#888;font-size:13px">验证码有效期 <strong>10 分钟</strong>，请勿泄露给他人。</p>
      <p style="color:#bbb;font-size:12px;margin-top:16px">如非本人操作，请忽略此邮件。</p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "GitHub Trending Agent - 邮箱验证码"
    msg["From"] = settings.smtp_user
    msg["To"] = email
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, [email], msg.as_string())
        logger.info(f"Verification code sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification code to {email}: {e}")
        return False


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
