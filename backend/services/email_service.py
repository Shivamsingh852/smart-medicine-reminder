import os


def send_email(to_email: str, subject: str, body: str) -> tuple[bool, str]:
    if not os.getenv("RESEND_API_KEY") or not os.getenv("EMAIL_FROM"):
        return False, "Email provider is not configured"
    try:
        import resend
        resend.api_key = os.environ["RESEND_API_KEY"]
        resend.Emails.send({"from": os.environ["EMAIL_FROM"], "to": [to_email], "subject": subject, "html": body})
        return True, "Email sent"
    except Exception as exc:
        return False, str(exc)
