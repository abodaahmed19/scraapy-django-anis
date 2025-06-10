from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from phonenumber_field.modelfields import PhoneNumberField

import uuid


def documents_upload_path(instance, filename):
    return f"company_docs/{instance.user.name}/documents/{filename}"


def additional_document_upload_path(instance, filename):
    return f"company_docs/{instance.business.user.name}/documents/{filename}"


class UserManager(BaseUserManager):

    def get_by_natural_key(self, email):
        return self.get(email=email)

    def create_superuser(self, email, password=None, **kwargs):
        while not password:
            password = input("Enter password: ")
            password_confirm = input("Confirm password: ")
            if password != password_confirm:
                print("Passwords do not match")
                password = None
                continue
        while User.objects.filter(email=email).exists():
            email = input("Enter a different email: ")

        user = self.create(
            email=email, is_superuser=True, is_staff=True, is_active=True, **kwargs
        )
        user.set_password(password)
        user.save()
        return user

    def create_user(self, email, password=None, **kwargs):
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = [
        ("individual", "Individual"),
        ("business", "Business"),
        ("driver", "Driver"),
        ("admin", "Admin"),
        ("staff", "Staff"),
        
    ]
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    name = models.CharField(max_length=100, help_text="Full name")
    email = models.EmailField(unique=True, max_length=100, help_text="Email address")
    lang = models.CharField(max_length=2, default="ar", help_text="Language")
    image = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    contact_number = PhoneNumberField(blank=True, null=True, help_text="Contact number")
    pickup_address = models.CharField(max_length=255, blank=True, null=True)  # 👈 nouveau champ

    date_joined = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    business_sub_type = models.CharField(
       max_length=50,
        blank=True,
        null=True,
        help_text="Sous‑type pour user_type='business'"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "user_type"]

    objects = UserManager()

    def __str__(self) -> str:
        if not self.name:
            return "anonymous | " + self.email
        return self.name + " | " + self.email

    def get_user_type(self) -> str:
        if self.is_staff:
            return "staff"
        return self.user_type

    @property
    def is_business(self) -> bool:
        return self.user_type == "business"

    @property
    def has_business_profile(self) -> bool:
        return hasattr(self, "business_profile")

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"


class BusinessProfile(models.Model):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="business_profile",
        limit_choices_to={"user_type": "business"},
    )
    address_line1 = models.CharField(max_length=100)
    address_line2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100)
    icon = models.ImageField(upload_to='business_icons/', blank=True, null=True)  # champ image

    longitude = models.DecimalField(
        max_digits=20, decimal_places=18, blank=True, null=True
    )
    latitude = models.DecimalField(
        max_digits=20, decimal_places=18, blank=True, null=True
    )
    on_site_contact_name = models.CharField(
        max_length=100, blank=True, null=True
    )
    on_site_contact_phone = models.CharField(
        max_length=20, blank=True, null=True
    )
    operational_address = models.CharField(
        max_length=1000, help_text="operational address", null=True, blank=True
    )
    primary_contact_person_name = models.CharField(
        max_length=100, help_text="address", null=True, blank=True
    )
    primary_contact_person_position = models.CharField(
        max_length=100, help_text="address", null=True, blank=True
    )
    primary_contact_person_contact_number = PhoneNumberField(
        help_text="Contact number", null=True, blank=True
    )
    primary_contact_person_email_address = models.CharField(
        max_length=100, help_text="address", null=True, blank=True
    )
    cr_number = models.CharField(max_length=10, help_text="cr_number", unique=True)
    vat_number = models.CharField(
        max_length=15, help_text="vat_number", unique=True, null=True, blank=True
    )
    cr_document = models.FileField(
        upload_to=documents_upload_path, null=True, blank=True
    )
    vat_document = models.FileField(
        upload_to=documents_upload_path, null=True, blank=True
    )
    mwan_license_number = models.CharField(
        max_length=15,
        help_text="Commercial registration number",
        unique=True,
        null=True,
        blank=True,
    )
    mwan_license_document = models.FileField(
        upload_to=documents_upload_path, null=True, blank=True
    )
    product_auto_accept = models.BooleanField(default=False)
    service_auto_accept = models.BooleanField(default=False)
    rental_auto_accept = models.BooleanField(default=False)


    def __str__(self) -> str:
        return self.user.name + " | " + self.cr_number


class BusinessAdditionalDocuments(models.Model):
    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="business_additional_documents",
    )
    name = models.CharField(max_length=150, help_text="document name")
    document = models.FileField(upload_to=additional_document_upload_path)

    def __str__(self) -> str:
        return self.business.user.name + " | " + self.name


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notification"
    )
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        ordering = ["created_at"]
        verbose_name = "notification"
        verbose_name_plural = "notifications"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses",null=True, blank=True)
    name = models.CharField(max_length=100, help_text="Address name")
    address_line1 = models.CharField(max_length=100)
    address_line2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100)
    longitude = models.DecimalField(
        max_digits=20, decimal_places=18, blank=True, null=True
    )
    latitude = models.DecimalField(
        max_digits=20, decimal_places=18, blank=True, null=True
    )
    on_site_contact_name = models.CharField(
        max_length=100, blank=True, null=True
    )
    on_site_contact_phone = models.CharField(
        max_length=20, blank=True, null=True
    )

    def __str__(self) -> str:
        return self.address_line1 + " | " + self.city + " | " + self.country
