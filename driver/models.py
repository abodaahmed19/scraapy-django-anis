from django.db import models
from django.conf import settings
from pms.models import User
from bms.models import OrderItem, TrackingSystemAddresses,OrderTracking

def documents_upload_path(instance, filename):
    return f"company_docs/{instance.user.name}/documents/{filename}"


class DriverProfile(models.Model):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
    ]
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drivers',limit_choices_to={"user_type": "business"}, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="driver_profile", limit_choices_to={"user_type": "driver"}, )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=APPROVED)
    id_number = models.CharField(max_length=20)
    contact_number = models.CharField(max_length=20,null=True, blank=True)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    model_year = models.CharField(max_length=10)
    plate_number = models.CharField(max_length=20)
    driver_id_file = models.FileField(upload_to=documents_upload_path, null=True, blank=True)
    driver_id_expiry = models.DateField(null=True, blank=True)
    license_file = models.FileField(upload_to=documents_upload_path, null=True, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    vehicle_registration_file = models.FileField(upload_to=documents_upload_path, null=True, blank=True)
    vehicle_registration_expiry = models.DateField(null=True, blank=True)
    insurance_file = models.FileField(upload_to=documents_upload_path, null=True, blank=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    # temp_password = models.CharField(max_length=100, null=True, blank=True)
    def __str__(self):
        return f"Driver: {self.user.name} | {self.plate_number}"
    

class DriverOrderTracking(models.Model):
    STARTED_JOURNEY = "started_journey"
    PICKED_UP = "picked_up"
    DROP_OFF = "dropped_off"

    STATUS = [
        (STARTED_JOURNEY," Started Journey"),

        (PICKED_UP,"Picked up" ),
        (DROP_OFF,"Dropped Off" ),
    ]


    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='tracking')
    tracking_system_address = models.ForeignKey(TrackingSystemAddresses, on_delete=models.CASCADE, related_name='driver_tracking')
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name='driver_tracking', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default=STARTED_JOURNEY)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
