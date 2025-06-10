from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'contact_number', 'is_active']
        extra_kwargs = {
            'contact_number': {'required': False, 'allow_null': True},  # ✅ Non requis
        }

class OTPVerifySerializer(serializers.Serializer):
    contact_number = serializers.CharField()
    otp = serializers.CharField()

    def validate(self, data):
        contact_number = data.get("contact_number")
        otp = data.get("otp")

        try:
            user = User.objects.get(contact_number=contact_number)
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur non trouvé.")

        if user.otp_code != otp:
            raise serializers.ValidationError("OTP invalide.")

        if user.is_active:
            raise serializers.ValidationError("Utilisateur déjà activé.")

        data["user"] = user
        return data