from django.contrib import admin
from .models import ScrapItem, ScrapImage, BankingInfo,OrderScrap


class ScrapImageInline(admin.TabularInline):
    model = ScrapImage
    readonly_fields = ['image_tag']
    extra = 0

    def image_tag(self, obj):
        if obj.image:
            return f'<img src="/assets/sms/{obj.image.name}" width="100"/>'
        return "-"
    image_tag.allow_tags = True
    image_tag.short_description = "Preview"

@admin.register(ScrapItem)
class ScrapItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'user', 'category_group', 'status', 'quantity']
    list_filter = ['status', 'category_group']
    search_fields = ['name', 'description', 'user__username']
    list_editable = ['status']
    inlines = [ScrapImageInline]

@admin.register(BankingInfo)
class BankingInfoAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'bank_name', 'iban_number', 'user']
    search_fields = ['full_name', 'iban_number', 'user__username']
class ScrapItemInline(admin.TabularInline):
    model = ScrapItem
    extra = 0
    readonly_fields = ['name', 'quantity', 'status']
    can_delete = False
    show_change_link = True

@admin.register(OrderScrap)
class OrderScrapAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'pickup_address', 'total_items', 'created_at']
    search_fields = ['user__email', 'pickup_address']
    list_filter = ['created_at']
    inlines = [ScrapItemInline]