from django.contrib import admin
from .models import Document , UserDocuments
# Register your models here.
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'uploaded_at']
    list_filter = ['id', 'type', 'uploaded_at']
    search_fields = ['id', 'type', 'uploaded_at']

admin.site.register(UserDocuments)