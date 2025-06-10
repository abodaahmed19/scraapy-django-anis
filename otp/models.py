from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

# Fonctions pour éviter les lambda non sérialisables
def default_created_at():
    return timezone.now()

def default_expires_at():
    return timezone.now() + timedelta(minutes=5)

User = get_user_model()

class PhoneOTP(models.Model):
    phone = models.CharField(max_length=15, unique=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=default_created_at)
    is_verified = models.BooleanField(default=False)  
    expires_at =  timezone.now() + timedelta(minutes=5)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.phone} - OTP: {self.otp}"


