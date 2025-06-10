
import requests
import logging
from django.conf import settings
from django.core.mail import send_mail


logger = logging.getLogger(__name__)

def send_otp_via_jawalbsms(phone: str, otp: str) -> bool:
    """
    Envoie l’OTP via l’API Jawalbosms.
    Renvoie True si la réponse contient '-100' (succès Jawalbosms), False sinon.
    """
    params = {
        "user":    settings.JAWALBSMS_USER,
        "pass":    settings.JAWALBSMS_PASS,
        "to":      phone,
        "message": f"Your confirmation code for registration is: {otp}",
        "sender":  settings.JAWALBSMS_SENDER,
    }
    try:
        resp = requests.get(settings.JAWALBSMS_APIURL, params=params, timeout=10)
        resp.raise_for_status()

        body = resp.text.lstrip("\ufeff").strip()
        logger.debug(f"[DEBUG] Jawalbosms response for {phone}: {repr(body)}")

        if "-100" in body:
            logger.info(f"SMS sent successfully to {phone}")
            return True
        else:
            logger.warning(f"Jawalbosms returned non-success code for {phone}: {body}")
            return False
    except Exception as e:
        logger.error(f"Jawalbosms SMS sending error for {phone}: {e}")
        return False


def send_otp_via_email(email: str, otp: str):
    subject = "Scraapy OTP CODE"
    message = f"Dear customer ,\n\nYour code OTP is : \n\nرمز التحقق الخاص بك لإستكمال التسجيل والدخول هو:\n\n{otp}\n\nThis code is valid for 90 second\n\nهذا الرمز صالح لمدة 90 ثانية."
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        print(f"[INFO] Email sent successfully to {email}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email to {email}: {e}")
        return False
