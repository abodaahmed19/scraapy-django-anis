from knox.settings import knox_settings
from knox.models import AuthToken
from rest_framework.serializers import DateTimeField

class TokenStrategy:
    @classmethod
    def obtain(cls, user):
        instance, token = AuthToken.objects.create(user=user)
        return {
            'token': token,
            'expiry': DateTimeField(format=knox_settings.EXPIRY_DATETIME_FORMAT).to_representation(instance.expiry),
            'user': user
        }
