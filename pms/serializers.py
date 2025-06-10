from rest_framework import serializers
from django.contrib.auth import authenticate
from djoser.serializers import UserSerializer as DjoserUserSerializer
from .models import BusinessAdditionalDocuments



from djoser.social.serializers import (
    ProviderAuthSerializer as SocialProviderAuthSerializer,
)
from phonenumber_field.serializerfields import PhoneNumberField
from .models import (
    User,
    BusinessProfile,
    BusinessAdditionalDocuments,
    Notification,
    Address,
)
from inventory.models import Item

from djoser.conf import settings as djoser_settings

from rest_framework import serializers
from django.contrib.auth import get_user_model
#from .models import BusinessDocument

User = get_user_model()

class BusinessAdditionalDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessAdditionalDocuments
        fields = '__all__'


class UserCreateSerializer(serializers.ModelSerializer):
    contact_number = PhoneNumberField(required=False, allow_null=True)
    business_sub_type = serializers.CharField(required=False, allow_blank=True)

    # Champs BusinessProfile
    cr_number = serializers.CharField(required=False)
    vat_number = serializers.CharField(required=False, allow_blank=True)
    address_line1 = serializers.CharField(required=False)
    address_line2 = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False)
    province = serializers.CharField(required=False)
    zip_code = serializers.CharField(required=False)
    country = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "user_type",
            "contact_number",
            "business_sub_type",
            # Champs BusinessProfile
            "cr_number",
            "vat_number",
            "address_line1",
            "address_line2",
            "city",
            "province",
            "zip_code",
            "country",
        ]

    def validate(self, attrs):
        contact = attrs.get("contact_number")

        if contact and User.objects.filter(contact_number=contact).exists():
            raise serializers.ValidationError({
                "contact_number": "Phone already exists"
            })

        if attrs.get("user_type") == "business":
            if not attrs.get("business_sub_type", "").strip():
                raise serializers.ValidationError({
                    "business_sub_type": "Ce champ est obligatoire pour les business."
                })

            required_business_fields = [
                "cr_number", "address_line1", "city", "province", "zip_code", "country"
            ]
            for field in required_business_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError({
                        field: f"{field} est obligatoire pour les business."
                    })

        return attrs

    def create(self, validated_data):
        contact = validated_data.pop("contact_number", None)
        sub = validated_data.pop("business_sub_type", None)
        raw_pw = "11111111"

        # Extraire les données du profil business
        business_fields = [
            "cr_number", "vat_number", "address_line1", "address_line2",
            "city", "province", "zip_code", "country"
        ]
        business_data = {field: validated_data.pop(field, None) for field in business_fields}

        # Création utilisateur
        user = User(**validated_data)
        user.contact_number = contact
        user.business_sub_type = sub
        user.set_password(raw_pw)
        user.is_active = False
        user.save()

        # Création BusinessProfile seulement si business
        if user.user_type == "business":
            BusinessProfile.objects.create(
                user=user,
                status=BusinessProfile.APPROVED,
                **business_data
            )

        return user




class BusinessProfileCRSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessProfile
        fields = ["cr_number"]

    def validate_cr_number(self, value):
        if not value:
            raise serializers.ValidationError("Commercial registration is required")
        if len(value) != 10:
            raise serializers.ValidationError(
                "Commercial registration must be 10 characters long"
            )
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        business_profile = BusinessProfile.objects.create(user=user, **validated_data)
        return business_profile


class BusinessProfileSerializer(serializers.ModelSerializer):
    additional_documents = serializers.SerializerMethodField()

    class Meta:
        model = BusinessProfile
        exclude = ["user"]

    def get_additional_documents(self, obj):
        documents = BusinessAdditionalDocuments.objects.filter(business=obj)
        return BusinessAdditionalDocumentsSerializer(documents, many=True).data


class BusinessProfileUpdateSerializer(serializers.ModelSerializer):
    additional_documents = BusinessAdditionalDocumentsSerializer(
        many=True, required=False
    )

    class Meta:
        model = BusinessProfile
        exclude = ["user", "status"]
        extra_kwargs = {
            "status": {"read_only": True},
        }
        read_only_fields = ["cr_number"]

    def validate_cr_number(self, value):
        if not value:
            raise serializers.ValidationError("Commercial registration is required")
        if len(value) != 10:
            raise serializers.ValidationError(
                "Commercial registration must be 10 characters long"
            )
        return value

    def validate_vat_number(self, value):
        if not value:
            raise serializers.ValidationError("VAT number is required")
        if len(value) != 15:
            raise serializers.ValidationError("VAT number must be 15 digits")
        if not (value.startswith("3") and value.endswith("3")):
            raise serializers.ValidationError("VAT number should start and end with 3")
        return value

    def validate_image(self, value):
        MAX_SIZE = 2 * 1024 * 1024
        if value.size > MAX_SIZE:
            raise serializers.ValidationError("Image size is too large")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        additional_documents_data = validated_data.pop('additional_documents', [])
        print("Additojnal " ,additional_documents_data )
        business_profile = BusinessProfile.objects.create(user=user, **validated_data)

        for doc_data in additional_documents_data:
            BusinessAdditionalDocuments.objects.create(business=business_profile, **doc_data)
        return business_profile

    def update(self, instance, validated_data):
        # Update fields dynamically
        for attr, value in validated_data.items():
            if attr == "additional_documents":
                continue  # Handle separately below
            setattr(instance, attr, value)

        instance.save()

        # Handle additional documents update
        if "additional_documents" in validated_data:
            additional_documents_data = validated_data["additional_documents"]

            # Delete existing additional documents
            instance.business_additional_documents.all().delete()

            # Create new additional documents
            for doc_data in additional_documents_data:
                BusinessAdditionalDocuments.objects.create(
                    business=instance, **doc_data
                )

        return instance
    
class BusinessProfileIconSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  # Corrigé ici
        fields = ['image']

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance



class UserSerializer(DjoserUserSerializer):
    business_profile = serializers.SerializerMethodField()
    user_type = serializers.CharField(source="get_user_type_display", read_only=True)
    contact_number = PhoneNumberField(required=False)

    def get_business_profile(self, obj):
        try:
            return BusinessProfileSerializer(obj.business_profile, context=self.context).data
        except BusinessProfile.DoesNotExist:
            return None

    def validate_name(self, value):
        if not value:
            raise serializers.ValidationError("Name is required")
        if len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters long")
        return value

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required")
        return value

    #def validate_password(self, value):
       # if not value:
            #raise serializers.ValidationError("Password is required")
        #if len(value) < 8:
           # raise serializers.ValidationError(
               # "Password must be at least 8 characters long"
           # )
        #return value

    def validate_user_type(self, value):
        if value not in User.USER_TYPE_CHOICES:
            raise serializers.ValidationError("Invalid user type")
        return value

    def validate_contact_number(self, value):
        return value

    def update(self, instance, validated_data):
        instance.contact_number = validated_data.get(
            "contact_number", instance.contact_number
        )
        instance.save()
        return super().update(instance, validated_data)

    class Meta:
        model = User
        fields = DjoserUserSerializer.Meta.fields + (
            "business_profile",
            "contact_number",
            "image",
            "user_type",
        )
        read_only_fields = DjoserUserSerializer.Meta.read_only_fields + (
            "user_type",
            "business_profile",
        )


class ProviderAuthSerializer(SocialProviderAuthSerializer):
    token = serializers.CharField(read_only=True)
    expiry = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)

    def create(self, validated_data):
        user = validated_data["user"]
        if not user.is_active:
            user.is_active = True
            user.save()
        return djoser_settings.SOCIAL_AUTH_TOKEN_STRATEGY.obtain(user)


class StaffVendorSerializer(UserSerializer):
    pending_items = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ("pending_items",)

    def get_pending_items(self, obj):
        return obj.items.filter(status=Item.PENDING).count()
    




class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        exclude = ["user"]


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"

    def create(self, validated_data):
        return Address.objects.create(**validated_data)

