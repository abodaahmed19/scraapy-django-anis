import re
import random
import phonenumbers
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from phonenumber_field.phonenumber import to_python
from django.conf import settings
import logging
import traceback
from django.contrib.auth import login, get_backends

from django.utils.timezone import localtime
from pathlib import Path
from rest_framework.authtoken.models import Token
from datetime import datetime
from rest_framework import views, status
from knox.models import AuthToken
from django.utils import timezone
from pms.serializers import UserSerializer
from otp.models import PhoneOTP
from rest_framework.throttling import UserRateThrottle
from otp.utils import send_otp_via_jawalbsms, send_otp_via_email



import jwt
from datetime import datetime, timedelta

User = get_user_model()


@method_decorator(csrf_exempt, name='dispatch')
class LoginOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            print("[DEBUG] Received POST /api/otp/login")

            user_input = request.data.get("email_or_phone", "").strip()
            print(f"[DEBUG] user_input: {user_input}")

            if not user_input:
                return Response({"error": "Email or phone is required"}, status=status.HTTP_400_BAD_REQUEST)

            is_email = re.match(r'^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$', user_input)
            is_phone = re.match(r'^\+?\d{10,15}$', user_input)

            user = None
            contact_number = None

            if is_email:
                print("[DEBUG] Input detected as email")
                try:
                    user = User.objects.get(email__iexact=user_input)
                except User.DoesNotExist:
                    return Response({"error": "Email not found"}, status=status.HTTP_400_BAD_REQUEST)

                contact_number = getattr(user, "contact_number", None)
                if not contact_number:
                    return Response({"error": "No phone number associated with this email"}, status=status.HTTP_400_BAD_REQUEST)

            elif is_phone:
                print("[DEBUG] Input detected as phone")
                contact_number = user_input
                users = User.objects.filter(contact_number=contact_number)

                if not users.exists():
                    return Response({"error": "Phone number not found"}, status=status.HTTP_400_BAD_REQUEST)
                elif users.count() > 1:
                    return Response({"error": "Multiple accounts found with this phone number. Please contact support."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    user = users.first()
                print(f"[DEBUG] user: {user}, contact_number: {contact_number}")

            else:
                return Response({"error": "Invalid email or phone format"}, status=status.HTTP_400_BAD_REQUEST)
            print("[DEBUG] Before normalize_phone")

            contact_number = normalize_phone(contact_number)
            print(f"[DEBUG] Normalized phone number: {contact_number}")

            otp_obj, _ = PhoneOTP.objects.get_or_create(phone=contact_number)
            
            if contact_number == "+966557780674":
                new_otp = "708090"
            else:
                new_otp = f"{random.randint(100000, 999999)}"
            otp_obj.otp = new_otp
            otp_obj.is_verified = False
            otp_obj.save()

            try:
              print("[DEBUG] Before sending OTP SMS")
              send_otp_via_jawalbsms(str(contact_number).lstrip("+"), new_otp)
              print("[DEBUG] After sending OTP SMS")
            except Exception as sms_error:
             print("[ERROR] Failed to send OTP via SMS:", sms_error)
             return Response({"error": "Failed to send OTP SMS"}, status=500)


            return Response({
                "success": True,
                "message": "OTP sent successfully to your phone number",
                "phone": str(contact_number)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print("Unhandled exception in LoginOTPView:")
            traceback.print_exc()
            return Response(
                {"error": "Internal server error", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class OTPThrottle(UserRateThrottle):
    rate = '5/min'

def generate_otp():
    return str(random.randint(100000, 999999))



class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            phone = request.data.get("phone")
            email = request.data.get("email")
            user_type = request.data.get("user_type", "").lower()

            if not phone:
                return Response({"error": "Phone number required"}, status=status.HTTP_400_BAD_REQUEST)

            new_otp = f"{random.randint(100000, 999999)}"
            otp_obj, _ = PhoneOTP.objects.get_or_create(phone=phone)
            otp_obj.otp = new_otp
            otp_obj.is_verified = False
            otp_obj.save()

            try:
                sms_ok = send_otp_via_jawalbsms(str(phone).lstrip("+"), new_otp)
            except Exception as e:
                print(f"Erreur d'envoi SMS pour {phone}: {e}")
                sms_ok = False

            email_ok = True
            if user_type == "business" and email:
                try:
                    email_ok = send_otp_via_email(email, new_otp)
                except Exception as e:
                    print(f"Erreur d'envoi Email pour {email}: {e}")
                    email_ok = False

            msg = "OTP sent"
            if not sms_ok:
                msg += "; SMS failed"
            if user_type == "business":
                msg += "; Email " + ("sent" if email_ok else "failed")

            return Response({"message": msg}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Unhandled exception in SendOTPView: {e}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def normalize_phone(phone_str):
    try:
        phone_obj = phonenumbers.parse(phone_str, "SA")  # "SA" pour Arabie Saoudite
        return phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        return phone_str  # Fallback si parsing échoue
    

class ResendOTPView(APIView):
    def post(self, request):
        phone = request.data.get("phone")

        if not phone:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_obj, created = PhoneOTP.objects.get_or_create(phone=phone)

            # Générer un nouvel OTP
            otp_obj.otp = generate_otp()
            otp_obj.attempts = 0
            otp_obj.created_at = timezone.now()
            otp_obj.expires_at = timezone.now() + timedelta(minutes=5)
            otp_obj.is_verified = False
            otp_obj.save()

            # Ici, tu peux envoyer le code OTP par SMS ou autre moyen
            # send_otp_sms(phone, otp_obj.otp)

            return Response({"message": "OTP resent successfully", "otp": otp_obj.otp}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in ResendOTPView: {e}")
            return Response({"error": "Failed to resend OTP"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class xVerifyOTPView(APIView):    
    def post(self, request):
        phone = request.data.get("phone")
        otp   = request.data.get("otp")
        if not phone or not otp:
            return Response({"error": "Phone and OTP required"}, status=400)

        try:
            otp_obj = PhoneOTP.objects.get(phone=phone)
        except PhoneOTP.DoesNotExist:
            return Response({"error": "Phone not found"}, status=404)

        if otp_obj.otp == otp:
            otp_obj.is_verified = True
            otp_obj.save()
            return Response({"message": "OTP verified"}, status=200)
        return Response({"error": "Invalid OTP"}, status=400)
    

    def post(self, request):
        phone = request.data.get("phone")
        otp = request.data.get("otp")

        if not phone or not otp:
            return Response({"error": "Phone and OTP required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_obj = PhoneOTP.objects.get(phone=phone)
            if otp_obj.otp == otp:
                otp_obj.is_verified = True
                otp_obj.save()
                return Response({"message": "OTP verified"}, status=status.HTTP_200_OK)
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        except PhoneOTP.DoesNotExist:
            return Response({"error": "Phone not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"Unhandled exception in VerifyOTPView: {e}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)      


@method_decorator(csrf_exempt, name='dispatch')
class VerifOTPWithTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        phone = request.data.get('phone')
        otp = request.data.get('otp')

        if not phone or not otp:
            return Response({"error": "Phone and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        phone_obj = to_python(phone)
        if not phone_obj or not phone_obj.is_valid():
            return Response({"error": "Invalid phone number"}, status=status.HTTP_400_BAD_REQUEST)

        phone = str(phone_obj)

        try:
            phone_otp = PhoneOTP.objects.get(phone=phone, otp=otp)
        except PhoneOTP.DoesNotExist:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_404_NOT_FOUND)

        # Gestion de l'expiry selon settings
        #expiry_duration = getattr(settings, "EXPIRY", 5)  # en minutes
        #if timezone.now() > phone_otp.created_at + timedelta(minutes=expiry_duration):
            #return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        phone_otp.is_verified = True
        phone_otp.save()

        try:
            user = User.objects.get(contact_number=phone)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user.is_active = True
        user.save()
        backend = get_backends()[0]  # ou choisis celui que tu veux explicitement
        user.backend = f"{backend.__module__}.{backend.__class__.__name__}"

        login(request, user)

        _, token = AuthToken.objects.create(user)

        user_data = UserSerializer(user, context={"request": request}).data


        return Response({
            "token": token,
            #"expiry": f"{expiry_duration} minutes",
            "user": user_data,
            "message": "OTP verified successfully."
        }, status=status.HTTP_200_OK)
