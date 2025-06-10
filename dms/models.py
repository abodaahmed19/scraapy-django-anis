from django.db import models
from pms.models import User
from inventory.models import Item
from bms.models import OrderItem,OrderItemReport
import uuid 
from django.core.files.storage import FileSystemStorage
from scraapy import settings

protected_upload_storage = FileSystemStorage(location=settings.PROTECTED_MEDIA_ROOT, base_url='/api/document/media/')

# Create your models here.
class Document(models.Model):
    DOCUMENT_TYPES = (
        ("reports", 'Reports'),
        ("contracts", 'Contracts'),
    )
    id = models.UUIDField(primary_key = True, default = uuid.uuid4, editable = False)
    type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True,)
    file = models.FileField(upload_to='documents/', storage=protected_upload_storage)
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="order_item_document", blank=True, null=True)

class UserDocuments(models.Model):
    FILE="file"
    JSON= "json"
    MARKDOWN="markdown"
    DOCUMENT_TYPES = [
    (FILE, 'file'),
    (JSON, 'json'),
    (MARKDOWN, 'markdown'),
    ]
    # CERTIFICATE="certificates"
    # CONTRACT="contracts"
    # REPORT = "reports"
    user = models.ForeignKey(User,on_delete=models.CASCADE, related_name="user_documents")
    type = models.CharField(max_length=10,choices=DOCUMENT_TYPES)
    created_at = models.DateTimeField(
        auto_now_add=True)
    order_item = models.ForeignKey(OrderItem,on_delete=models.CASCADE, related_name="documents_meta")
    order_item_report = models.ForeignKey(OrderItemReport,on_delete=models.CASCADE ,related_name="report_meta_data",blank=True, null=True)
