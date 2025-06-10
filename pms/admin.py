from django.contrib import admin
from .models import User, BusinessProfile, BusinessAdditionalDocuments, Address,Notification


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "name",
        "user_type",
        "lang",
        "contact_number",
        "date_joined",
        "is_active",
        "is_staff",
        "is_superuser",
    ]
    list_filter = ["user_type", "lang", "is_active", "is_staff", "is_superuser"]
    search_fields = ["name", "email", "contact_number"]
    readonly_fields = ["date_joined"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "email",
                    "user_type",
                    "lang",
                    "image",
                    "contact_number",
                )
            },
        ),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "cr_number", "status"]
    list_filter = ["status"]
    # search_fields = ['user', 'cr_number']
    # readonly_fields = ['user']
    # fieldsets = (
    #     (None, {
    #         'fields': ('user', 'cr_number', 'status')
    #     }),
    # )


@admin.register(BusinessAdditionalDocuments)
class BusinessAdditionalDocumentsAdmin(admin.ModelAdmin):
    list_display = ["name", "business"]
    list_filter = ["name", "business"]
    search_fields = ["name", "business"]
    readonly_fields = ["name", "business"]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "business",
                )
            },
        ),
    )


admin.site.register(Address)
admin.site.register(Notification)