import os
from uuid import uuid4
from django.db import models
from django.conf import settings
from inventory.models import Category
from pms.models import User  # ou settings.AUTH_USER_MODEL si tu préfères
# Assure-toi que BankingInfo est bien importé si elle est dans une autre app

# 👇 Fonction placée en haut pour qu'elle soit reconnue
def custom_asset_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid4().hex}.{ext}"
    return os.path.join('assets/sms/', filename)


class BankingInfo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150)
    bank_name = models.CharField(max_length=100)
    iban_number = models.CharField(max_length=24)  # Longueur fixe IBAN KSA : SA + 22 chiffres

    def save(self, *args, **kwargs):
        if not self.iban_number.startswith("SA") or len(self.iban_number) != 24:
            raise ValueError("L'IBAN doit commencer par 'SA' et contenir exactement 24 caractères.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.bank_name}"


class ScrapItem(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('treated', 'Treated'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category_group = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    banking_info = models.ForeignKey(BankingInfo, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey('OrderScrap', on_delete=models.CASCADE, null=True, blank=True, related_name="scrap_items")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    name = models.CharField(max_length=100)
    size = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    description = models.TextField(max_length=500)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.name} ({self.quantity}) - {self.status}"



class ScrapImage(models.Model):
    scrap_item = models.ForeignKey(ScrapItem, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=custom_asset_upload_path)

    def __str__(self):
        return f"Image for {self.scrap_item.name}"

# models.py

class OrderScrap(models.Model):
    STATUS_CHOICES = [
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PENDING', 'Pending'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pickup_address = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # 💰 nouveau champ
    total_items = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.pk} by {self.user.email}"
