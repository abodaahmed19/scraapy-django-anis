import uuid
from django.db import models
from django.utils.html import mark_safe
from pms.models import User, BusinessProfile
from inventory.utils import (
    get_item_image_path,
    get_categorygroup_icon_path,
    get_field_type_icon_path,
    mds_upload_path,
    rental_documents_upload_path, 
    get_item_document_path,
)

from django.core.exceptions import ValidationError
from decimal import Decimal, ROUND_DOWN


def validate_price_unit(value):
    # only allow 'unit' or 'unit'/'unit' format
    if value.count('/') > 1:
        raise ValidationError(
            ('Price unit can only have one "/" character'),
            params={'value': value},
        )
    if value.count('/') == 1:
        unit1, unit2 = value.split('/')
        if not unit1 or not unit2:
            raise ValidationError(
                ('Price unit cannot have empty units'),
                params={'value': value},
            )


class CategoryGroup(models.Model):
    PRODUCT = 'product'
    RENTAL = 'rental'
    SERVICE = 'service'
    LISTING_TYPE_CHOICES = [
        (PRODUCT, 'Product'),
        (RENTAL, 'Rental'),
        (SERVICE, 'Service'),
    ]
    LISTING_TYPE_CHOICES_AR = [
        (PRODUCT, 'منتج'),
        (RENTAL, 'تأجير'),
        (SERVICE, 'خدمة'),
    ]
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    name = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100)
    group_type = models.CharField(max_length=10, choices=LISTING_TYPE_CHOICES)
    icon = models.FileField(
        upload_to=get_categorygroup_icon_path, blank=True, null=True
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=PENDING
    )

    def __str__(self):
        return self.name

    def icon_tag(self):
        if not self.icon:
            return ''
        return mark_safe(
            f'<img src="{self.icon.url}" width="50" height="50" />'
        )


class FieldType(models.Model):
    TEXT = 'text'
    NUMBER = 'number'
    FILE = 'file'
    DATA_TYPE_CHOICES = [
        (TEXT, 'Text'),
        (NUMBER, 'Number'),
        (FILE, 'File'),
    ]

    data_type = models.CharField(
        max_length=10, choices=DATA_TYPE_CHOICES, default='text'
    )


    icon = models.FileField(
        upload_to=get_field_type_icon_path, blank=True, null=True
    )
    name = models.CharField(max_length=100, unique=True)
    name_ar = models.CharField(max_length=100)
    valid_options = models.CharField(max_length=2000, blank=True, null=True)

    def __str__(self):
        return self.name

    def clean(self):
        if self.valid_options:
            clean_options = [
                option.strip().lower()
                for option in self.valid_options.split(',')
            ]
            if len(set(clean_options)) != len(clean_options):
                raise ValidationError(
                    {
                        'valid_options': 'Field type valid options must be unique'
                    }
                )

    def icon_tag(self):
        if not self.icon:
            return ''
        return mark_safe(
            f'<img src="{self.icon.url}" width="50" height="50" />'
        )


class Category(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    FLEET = 'fleet'
    SUBITEM_TYPE_CHOICES = [
        (FLEET, 'Fleet'),
    ]
    status = models.CharField(
    max_length=10, choices=STATUS_CHOICES, default=APPROVED
    )
    category_group = models.ForeignKey(
        CategoryGroup, on_delete=models.CASCADE, related_name='categories'
    )
    name = models.CharField(max_length=100, unique=True)
    name_ar = models.CharField(max_length=100)
    price_unit = models.CharField(
        max_length=100, validators=[validate_price_unit]
    )
    price_unit_ar = models.CharField(
    max_length=100, validators=[validate_price_unit],
    null=True, blank=True
    )
    field_types = models.ManyToManyField(
        'FieldType', related_name='categories', blank=True
    )
    sub_item_type = models.CharField(
        max_length=10, choices=SUBITEM_TYPE_CHOICES, blank=True, null=True
    )
    associated_categories = models.ManyToManyField('self', symmetrical=True,blank=True) 

    legal_requirements = models.ManyToManyField('LegalRequirements', related_name='categories', blank=True)
    # this is for the front to hide the price of the item if the user is not logged in
    hide_price = models.BooleanField(default=False)
    require_contract = models.BooleanField(default=False)
    contract_text = models.TextField(blank=True, null=True)
    send_certificate = models.BooleanField(default=False) 
    # vehicle_specs = models.ManyToManyField(VehicleSpecs, related_name="categories", blank=True)  # ✅ تم النقل هنا
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories',null=True,blank=True)

    def __str__(self):
        return self.name
    

def validate_user_fields(value):
    valid_fields = [field.name for field in BusinessProfile._meta.get_fields()]
    invalid_fields = [field for field in value if field not in valid_fields]
    
    if invalid_fields:
        raise ValidationError(f"Invalid field names in requirements: {', '.join(invalid_fields)}")

class VehicleSpecs(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ] 
    make = models.CharField(max_length=100)  
    model = models.CharField(max_length=100)  
    model_year = models.CharField(max_length=100)  
    categories = models.ForeignKey(Category,on_delete=models.CASCADE,related_name="vehicle_specs")
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending"
    )
    
    
    # @property
    # def status(self):
    #     return [category.status for category in self.categories.all()] 

    def __str__(self):
        return f"{self.make} {self.model} ({self.model_year})"
    
 # item=models.OneToOneField(Item,on_delete=models.CASCADE,re)
 
class LegalRequirements(models.Model):
    name = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=100,null=True, blank=True)
    description = models.CharField(max_length=2000, blank=True, null=True)  
    # Use a JSONField to store a list of field names or an ArrayField if using PostgreSQL
    requirements = models.JSONField(validators=[validate_user_fields], blank=True, null=True)
    
    def __str__(self):
        return self.name



class ExtraField(models.Model):
    type = models.ForeignKey(
        FieldType, on_delete=models.CASCADE, related_name='extra_fields'
    )
    value = models.CharField(max_length=100,blank=True, null=True)
    item = models.ForeignKey('Item', on_delete=models.CASCADE , related_name='item_extra_field')
    file_value = models.FileField(upload_to=get_item_document_path, blank=True, null=True)


    def __str__(self):
        # Show a summary depending on the field type
        if self.type.data_type == 'file' and self.file_value:
            return f"{self.type.name} | File Uploaded"
        return f"{self.type.name} | {self.value}"

    def clean(self):
        if self.type.data_type == 'file':
            if not self.file_value:
                raise ValidationError({
                    'file_value': 'This field requires a file upload.'
                })
        else:
            if not self.value:
                raise ValidationError({
                    'value': 'This field requires a value.'
                })
            if self.type.valid_options:
                clean_options = [
                    option.strip().lower() for option in self.type.valid_options.split(',')
                ]
                if self.value.lower() not in clean_options:
                    raise ValidationError({
                        'value': 'Invalid field value, must be one of type valid options'
                    })



    def __str__(self):
        return self.name

 
class Item(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=2000, blank=True, null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, default=0.00
    )


    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    vehicle_specs = models.ForeignKey(VehicleSpecs, on_delete=models.SET_NULL, null=True, blank=True)


    longitude = models.DecimalField(
        max_digits=20, decimal_places=18, blank=True, null=True
    )
    latitude = models.DecimalField(
        max_digits=20, decimal_places=18, blank=True, null=True
    )
    address_line1 = models.CharField(max_length=100, null=True , blank=True)
    address_line2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100 , null=True , blank=True)
    zip_code = models.CharField(max_length=10 , null=True , blank=True)
    country = models.CharField(max_length=100)
    on_site_contact_name = models.CharField(
        max_length=100, blank=True, null=True
    )
    on_site_contact_phone = models.CharField(
        max_length=20, blank=True, null=True
    )

    on_site_pickup = models.BooleanField(default=False)
    quantity = models.IntegerField(null=True, blank=True)

    minimum_selling_quantity = models.FloatField(default=0,null=True,blank=True)
    
    mds_document = models.FileField(
        upload_to=mds_upload_path, blank=True, null=True
    )

    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='items'
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=PENDING
    )
    staff_note = models.CharField(max_length=2000, blank=True, null=True)
    last_max_quantity = models.IntegerField(null=True, blank=True)


    # rent_item_info = models.ForeignKey(RentItemInfo, on_delete=models.CASCADE, related_name='item_rent_item_info', blank=True, null=True)
     
    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name

    @property
    def extra_fields(self):
        return ExtraField.objects.filter(item=self)
    
    @property
    def price_after_discount(self):
        return (self.price - self.discount.quantize(
            Decimal('0.00'), rounding=ROUND_DOWN
        ))

    def image_tag(self):
        if not self.image:
            return ''
        return mark_safe(
            f'<img src="{self.image.url}" width="50" height="50" />'
        )
    
    def clean(self):
        super().clean()

        if self.category.category_group.group_type == CategoryGroup.SERVICE or self.category.category_group.group_type == CategoryGroup.RENTAL:
            self.quantity = 1
            self.minimum_selling_quantity = 1
        else: 

            if self.minimum_selling_quantity < 0:
                self.minimum_selling_quantity = 0

            elif self.minimum_selling_quantity > self.quantity:
                self.minimum_selling_quantity = self.quantity

        # if not self.pk:  # This is a new item being created
        #     if self.quantity is not None:
        #         self.last_max_quantity = self.quantity
        # else:  # This is an existing item being updated
        #     try:
        #         original_item = Item.objects.get(pk=self.pk)
        #         if self.quantity is not None and original_item.quantity is not None:
        #             if self.quantity > original_item.quantity:  
        #                 self.last_max_quantity = self.quantity
        #     except Item.DoesNotExist:
        #         pass
        


class Image(models.Model):
    image = models.ImageField(upload_to=get_item_image_path)
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name='images'
    )
    is_thumbnail = models.BooleanField(default=False)

    def __str__(self):
        return self.image.url


class SubItem(models.Model):
    
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='sub_items',
        limit_choices_to={
            'category__sub_item_type': Category.SUBITEM_TYPE_CHOICES
        },
    )
    value = models.CharField(max_length=100)
    numberPlate = models.CharField(max_length=1000, null=True, blank=True)
    # files = models.ForeignKey('UploadFilesSubItem', blank=True)


    def __str__(self):
        return (
            self.item.category.name
            + ' '
            + self.item.category.sub_item_type
            + ' item('
            + str(self.id)
            + ')'
        )
        
    # def add_file(self, file_name, expiry_date):
        
    #     if self.files is None:
    #         self.files = []
    #     self.files.append({"filename": file_name, "expiry_date": expiry_date})
    #     self.save()    

class CertificateType(models.Model):
    name = models.CharField(max_length=255, unique=True)  # اسم الشهادة
    description = models.TextField(null=True, blank=True)  # وصف اختياري للشهادة

    def __str__(self):
        return self.name
    
class UploadFilesSubItem(models.Model):
    subitem = models.ForeignKey(SubItem, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to=rental_documents_upload_path)  # ✅ حفظ الملف فعليًا
    expiry_date = models.DateField(null=True, blank=True)  # ✅ تاريخ انتهاء لكل ملف
    certificate_type = models.ForeignKey(CertificateType, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.file.name} - {self.certificate_type.name if self.certificate_type else 'No Certificate'}"
        # return self.file.name

class UploadImagesSubItems(models.Model):
    subitem = models.ForeignKey(SubItem, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=rental_documents_upload_path)
    is_thumbnail = models.BooleanField(default=False)

    def __str__(self):
        return self.image.name
