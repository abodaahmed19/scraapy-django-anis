from django.db import models
from pms.models import User
from django.core.exceptions import ValidationError
import uuid
from inventory.models import Category, CategoryGroup, FieldType, Item
from inventory.utils import get_item_image_path, mds_upload_path
from .utils import order_item_report_path
from decimal import Decimal, ROUND_DOWN
from scraapy import settings
from pms.models import Address


# For migration /usr/src/app/bms/migrations/0001_initial.py
def validate_numeric_11_digits(value):
    if not value.isdigit() or len(value) != 11:
        raise ValidationError("Contract number must be exactly 11 numeric digits.")

class CategoryShippingRate(models.Model):
    category = models.OneToOneField(
        Category, on_delete=models.CASCADE, related_name='shipping_rate'
    )
    rate_per_km = models.DecimalField(max_digits=6, decimal_places=2, default=5)

    def __str__(self):
        return f"Shipping Rate for {self.category.name}: {self.rate_per_km} per km"


class Order(models.Model):
    NOT_PAID = "notpaid"
    PAID = "paid"
    PENDING = "pending"
    COMPLETED = "completed"

    STATUS = (
        (NOT_PAID, "Not paid"),
        (PAID, "Paid"),
        (PENDING, "Pending"),
        (COMPLETED, "Completed"),
    )
    SHIPPING_OPTIONS = [
    ('standard', 'Standard Shipping'),
    ('express', 'Express Shipping'),
    ('pickup', 'In-store Pickup'),
]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=STATUS, default=PENDING)
    payment_date = models.DateTimeField(null=True, blank=True)

    shipping_option = models.CharField(max_length=50, choices=SHIPPING_OPTIONS, null=True, blank=True)
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="order_buyer",
        blank=True,
        null=True,
    )
    buyer_email = models.EmailField(null=True, blank=True)

    is_delivery = models.BooleanField(default=False)

    delivery_address_line1 = models.CharField(max_length=100,blank=True, null=True)

    delivery_address_line2 = models.CharField(max_length=100, blank=True, null=True)
    delivery_city = models.CharField(max_length=100, blank=True, null=True)
    delivery_province = models.CharField(max_length=100,blank=True, null=True)
    delivery_zip_code = models.CharField(max_length=10,blank=True, null=True)
    delivery_country = models.CharField(max_length=100,blank=True, null=True)
    delivery_charges = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    longitude = models.DecimalField(max_digits=20, decimal_places=18, blank=True, null=True)
    latitude = models.DecimalField(max_digits=20, decimal_places=18, blank=True, null=True)
    delivery_contact_name = models.CharField(max_length=100, blank=True, null=True)
    delivery_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    addressName = models.CharField(max_length=100, blank=True, null=True,help_text="Address name")

    zatca_qr = models.CharField(max_length=255, blank=True, null=True)
    base64_invoice = models.CharField(max_length=255, blank=True, null=True)
    invoice_hash = models.CharField(max_length=255, blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)


    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.id)

    @property
    def items(self):
        return self.order_items.all()

    @property
    def total_price(self):
        total = 0
        for item in self.order_items.all():
            item_total_price = item.price * item.order_quantity
            total = total + item_total_price
        return total

    @property
    def total_discount(self):
        discount = 0
        for item in self.order_items.all():
            discount = discount + item.total_discount
        return discount

    @property
    def total_price_after_discount(self):
        return self.total_price - self.total_discount

    @property
    def tax_amount(self):
        return (self.total_price_after_discount * settings.VAT).quantize(
            Decimal("0.00"), rounding=ROUND_DOWN
        )

    @property
    def total_with_tax(self):
        return self.total_price_after_discount + self.tax_amount


class OrderItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=2000, blank=True, null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, default=0.00
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    mds_document = models.FileField(upload_to=mds_upload_path, blank=True, null=True)
    
    address_line1 = models.CharField(max_length=100)
    address_line2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100)
    on_site_contact_name = models.CharField(max_length=100, blank=True, null=True)
    on_site_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    on_site_pickup = models.BooleanField(default=False)
    quantity = models.IntegerField()
    order_quantity = models.IntegerField()
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="order_item_owner"
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="order_item")
    staff_note = models.CharField(max_length=2000, blank=True, null=True)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items"
    )
    parent_order_item = models.ForeignKey(
        "OrderItem",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="aditional_services",
    )
    tracking_system_addresses = models.ForeignKey(
        "TrackingSystemAddresses",
        on_delete=models.CASCADE,
        related_name="order_item_addresses",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name

    @property
    def total_price(self):
        total = self.price * self.order_quantity
        return total

    @property
    def total_discount(self):
        discount = (self.discount * self.order_quantity).quantize(
            Decimal("0.00"), rounding=ROUND_DOWN
        )
        return discount

    @property
    def total_price_after_discount(self):
        return self.total_price - self.total_discount


class OrderItemExtraField(models.Model):
    type = models.ForeignKey(
        FieldType,
        on_delete=models.CASCADE,
        related_name="order_item_extra_fields",
    )
    value = models.CharField(max_length=100)
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, related_name="extra_fields"
    )

    def __str__(self):
        return self.type.name + " | " + self.value

    def clean(self):
        if self.type not in self.order_item.category.field_types.all():
            raise ValidationError(
                {"type": "Field type not allowed for this item category"}
            )
        if self.type.valid_options:
            clean_options = [
                option.strip().lower() for option in self.type.valid_options.split(",")
            ]
            if self.value.lower() not in clean_options:
                raise ValidationError(
                    {"value": "Invalid field value, must be one of type valid options"}
                )


class OrderItemImage(models.Model):
    image = models.ImageField(upload_to=get_item_image_path)
    item = models.ForeignKey(
        OrderItem, on_delete=models.CASCADE, related_name="order_item_image"
    )
    is_thumbnail = models.BooleanField(default=False)

    def __str__(self):
        return self.image.url


class OrderSubItem(models.Model):
    item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="order_sub_item",
        limit_choices_to={"category__sub_item_type": Category.SUBITEM_TYPE_CHOICES},
    )
    value = models.CharField(max_length=100)

    def __str__(self):
        return (
            self.item.category.name
            + " "
            + self.item.category.sub_item_type
            + " item("
            + str(self.id)
            + ")"
        )


class OrderTracking(models.Model):
    REVIEWING = "reviewing"
    COMPLETE = "complete"
    RECEIVED = "received"

    # product statuses
    PREPARING = "preparing"
    READY = "ready"
    SHIPPED = "shipped"
    STARTED_JOURNEY = "started_journey"
    PICKED_UP = "picked_up"
    DROP_OFF = "dropped_off"
    # rental statuses
    ACCEPTED = "accepted"
    LOANED = "loaned"
    RETURNED = "returned"
    # service statuses
    OBTAINED = "obtained"
    INSPECTING = "inspecting"
    HANDOFF = "handoff"

    PRODUCT_STATUS = [
        (REVIEWING, "seller"),
        (PREPARING, "seller"),
        (READY, "driver"),
        (STARTED_JOURNEY,"driver"),
        (PICKED_UP, "driver"),
        (DROP_OFF,"buyer"),
        # (RECEIVED, "buyer"),
        (COMPLETE, ""),
    ]

    PRODUCT_PICKUP_STATUS = [
        (REVIEWING, "seller"),
        (PREPARING, "seller"),
        (READY,"buyer"),
        (RECEIVED, "buyer"),
        (COMPLETE, ""),
    ]

    RENTAL_STATUS = [
        (REVIEWING, "seller"),
        (ACCEPTED, "seller"),
        (LOANED, "buyer"),
        (RETURNED, "seller"),
        (COMPLETE, ""),
    ]

    SERVICE_STATUS = [
        (REVIEWING, "seller"),
        (OBTAINED, "seller"),
        (INSPECTING, "seller"),
        (HANDOFF, "buyer"),
        (COMPLETE, ""),
    ]

    order_item = models.OneToOneField(
        OrderItem, on_delete=models.CASCADE, related_name="tracking"
    )
    status = models.CharField(default=REVIEWING,max_length=50)
    @property
    def require_file(self):
        if self.status== self.INSPECTING:
            return True
        return False
    @property
    def steps(self):
        if self.order_item.category.category_group.group_type == CategoryGroup.PRODUCT:
            # print("the shipping option:",self.order_item.order.shipping_option)
            if self.order_item.order.shipping_option == 1:
                return self.PRODUCT_STATUS
            return self.PRODUCT_PICKUP_STATUS
        elif self.order_item.category.category_group.group_type == CategoryGroup.RENTAL:
            return self.RENTAL_STATUS
        elif (
            self.order_item.category.category_group.group_type == CategoryGroup.SERVICE
        ):
            return self.SERVICE_STATUS


class TrackingSystemAddresses(models.Model):
    
    pickup_address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name="TrackingSystemAddresses_pickup", null=True, blank=True)
    destination_address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name="TrackingSystemAddresses_destination")



class OrderItemReport(models.Model):
    order_item=models.ForeignKey(OrderItem,on_delete=models.CASCADE,related_name="order_item_report")
    report=models.FileField(upload_to=order_item_report_path, blank=True, null=True)
    created_at = models.DateTimeField(
    auto_now_add=True,
    )

