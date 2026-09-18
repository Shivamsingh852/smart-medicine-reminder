import os


def send_sms(phone_number: str, message: str) -> tuple[bool, str]:
    if not all(os.getenv(key) for key in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER")):
        return False, "SMS provider is not configured"
    try:
        from twilio.rest import Client
        client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
        client.messages.create(body=message, from_=os.environ["TWILIO_PHONE_NUMBER"], to=phone_number)
        return True, "SMS sent"
    except Exception as exc:
        return False, str(exc)
