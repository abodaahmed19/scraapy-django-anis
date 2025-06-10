from rest_framework import serializers
from .models import (
    CertificateType,
    Item,
    SubItem,
    ExtraField,
    FieldType,
    Category,
    CategoryGroup,
    Image,
    LegalRequirements,
    UploadFilesSubItem,
    UploadImagesSubItems,
    VehicleSpecs
    
)
import json

from pms.models import User
import math



# class FieldTypeSerializer(serializers.ModelSerializer):
#     valid_options = serializers.SerializerMethodField()
   


#     class Meta:
#         model = FieldType
#         fields = ['name', 'icon', 'valid_options']  

#     def get_valid_options(self, obj):
        
#         # if obj.valid_options:
#         #     try:
#         #         return json.loads(obj.valid_options)  
#         #     except json.JSONDecodeError:
#         #         return obj.valid_options  #
#         # return None 
#         return obj.get_valid_options_as_list()
    
class FieldTypeSerializer(serializers.ModelSerializer):
    valid_options = serializers.SerializerMethodField()

    class Meta:
        model = FieldType
        fields = ['name', 'icon', 'valid_options']

    def get_valid_options(self, obj):
        if not obj.valid_options:
            return []  

        try:
            
            options = json.loads(obj.valid_options)

            
            if isinstance(options, (list, dict)):
                return options
            
            
            return [options]

        except json.JSONDecodeError:
            
            formatted_options = obj.valid_options.strip("[]").replace("'", "").split(", ")

            
            if obj.valid_options.startswith("{") and obj.valid_options.endswith("}"):
                try:
                    return json.loads(obj.valid_options.replace("'", '"'))  # تحويل القيم المفردة
                except json.JSONDecodeError:
                    pass  
            
            return formatted_options  

class ExtraFieldSerializer(serializers.ModelSerializer):
    type = FieldTypeSerializer(read_only=True)
    name = serializers.CharField(write_only=True)
    value = serializers.CharField(required=False)
    file_value = serializers.FileField(required=False)

    class Meta:
        model = ExtraField
        fields = ['value', 'type', 'name', 'file_value']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.type.data_type == FieldType.FILE:
            request = self.context.get('request')
            if instance.file_value:
                file_url = instance.file_value.url
                if request:
                    file_url = request.build_absolute_uri(file_url)
                representation['value'] = file_url
            else:
                representation['value'] = None
        return representation
    
class CertificateTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateType
        fields = ['id', 'name', 'description']
        
class UploadFilesSubItemSerializer(serializers.ModelSerializer):
    certificate_type = CertificateTypeSerializer(read_only=True)
    certificate_type_id = serializers.PrimaryKeyRelatedField(
        queryset=CertificateType.objects.all(), write_only=True, source='certificate_type'
    )
    
    
    class Meta:
        model = UploadFilesSubItem
        fields = ['file', 'expiry_date', 'certificate_type', 'certificate_type_id']

class UploadImagesSubItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadImagesSubItems
        fields = ['id', 'image', 'is_thumbnail']   
   
        
class SubItemSerializer(serializers.ModelSerializer):
    files = UploadFilesSubItemSerializer(many=True, required=False)
    temp_value = serializers.CharField(write_only=True, required=False)
    images = UploadImagesSubItemSerializer(many=True, read_only=True)



    class Meta:
        model = SubItem
        fields = ['value', 'numberPlate','files','images','id',"temp_value"]
            
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # نرجع نفس temp_value اللي استقبلناه من الفرونت
        if hasattr(self, 'initial_data') and 'temp_value' in self.initial_data:
            data['temp_value'] = self.initial_data['temp_value']
        return data


            
    def create(self, validated_data):
            print("🔥 Received data:", json.dumps(validated_data, indent=4, ensure_ascii=False))

            # 1️⃣ استخرج بيانات الملفات من حقل files
            files_data = validated_data.pop('files', [])  
            validated_data.pop('temp_value', None) 
            
            # 2️⃣ أنشئ الـ SubItem بدون أي ملفات
            sub_item = SubItem.objects.create(**validated_data)

            # 3️⃣ أنشئ UploadFilesSubItem لكل ملف وأضف subitem=sub_item
            for file_data in files_data:
                UploadFilesSubItem.objects.create(
                    subitem=sub_item, 
                    **file_data
                )
            
            return sub_item

    def update(self, instance, validated_data):
        print("🔥 Updating sub_item:", instance.id)
        files_data = validated_data.pop('files', None)

        
        if files_data is not None:
            UploadFilesSubItem.objects.filter(subitem=instance).delete()

            
            for file_data in files_data:
                UploadFilesSubItem.objects.create(
                    subitem=instance,
                    **file_data
                )

        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
        
        

class CategoryGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryGroup
        fields = ['id', 'name','name_ar', 'icon', 'group_type','status']





class legalRequirementsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegalRequirements

        fields = ['id', 'name','description','requirements']
        
class VehicleSpecsSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleSpecs
        fields = ["make", "model", "model_year","status"]        

class CategorySerializer(serializers.ModelSerializer):
    extra_field_types = FieldTypeSerializer(
        many=True, read_only=True, source='field_types'
    )
    vehicle_specs = VehicleSpecsSerializer(many=True, read_only=True)
    # def get_vehicle_specs(self, obj):
    #     specs = obj.vehicle_specs.filter(status="approved").first()  
    #     return VehicleSpecsSerializer(specs).data if specs else None
    
    legal_requirements = legalRequirementsSerializer(many=True, read_only=True,required=False)
    category_group = CategoryGroupSerializer()
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'name_ar',
            'price_unit',
            'price_unit_ar',
            'extra_field_types',
            "vehicle_specs",
            'sub_item_type',
            'status',
            'category_group',
            'legal_requirements',
            'hide_price',
            'require_contract',
            'contract_text'
            
        ]
        
    def update(self, instance, validated_data):
        category_group_data = validated_data.pop('category_group', None)
        setattr(instance,'status',Category.APPROVED)
        for field, value in validated_data.items():
            setattr(instance, field, value) 
        setattr(instance,'status',Category.APPROVED)
        if category_group_data:
            category_group = instance.category_group
            for field, value in category_group_data.items():
                setattr(category_group, field, value) 
            if category_group.status == CategoryGroup.PENDING:
                setattr(category_group,'status',CategoryGroup.APPROVED)
            category_group.save()
        instance.save()
        return instance       



class CategoryGroupSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = CategoryGroup
        fields = ['id', 'name', 'name_ar', 'icon', 'categories']

class ApprovedCategoryGroupSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()

    class Meta:
        model = CategoryGroup
        fields = ['id', 'name', 'name_ar', 'icon', 'categories']
    def get_categories(self, obj):
        return CategorySerializer(obj.categories.filter(status=Category.APPROVED),many=True).data



class CategoryGroupFilteringSerializer(serializers.ModelSerializer):

    class Meta:
        model = CategoryGroup
        fields = ['id', 'name', 'name_ar', 'icon']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['categories'] = CategorySerializer(
            instance.categories.filter(status=Category.APPROVED), 
            many=True, 

        ).data
        return data

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'image', 'is_thumbnail']

    def validate_image(self, value):
        MAX_SIZE = 2 * 1024 * 1024
        if value.size > MAX_SIZE:
            raise serializers.ValidationError('Image size is too large')


        if len(value.name) > 100:
            value.name = value.name[-100:]



        return value

    def validate_is_thumbnail(self, value):
        return value

    def create(self, validated_data):
        item = self.context['item']
        image = Image.objects.create(item=item, **validated_data)
        return image

    def update(self, instance, validated_data):
        instance.is_thumbnail = validated_data.get(
            'is_thumbnail', instance.is_thumbnail
        )
        instance.save()
        return instance

class PostItemSerializer(serializers.ModelSerializer):
    extra_fields = ExtraFieldSerializer(many=True, required=False)
    sub_items = SubItemSerializer(many=True, required=False)
    owner_name = serializers.SerializerMethodField()
    owner_image = serializers.SerializerMethodField()
    images = ImageSerializer(many=True, read_only=True)
    price_unit = serializers.SerializerMethodField()
    category_type = serializers.CharField(
        source='category.category_group.group_type', read_only=True
    )
    new_category_listing_type = serializers.ChoiceField(
        choices=CategoryGroup.LISTING_TYPE_CHOICES, required=False
    )
    new_category = serializers.CharField(
        max_length=100, write_only=True, required=False
    )
    new_sub_category = serializers.CharField(
        max_length=100, write_only=True, required=False
    )

    vehicle_specs = VehicleSpecsSerializer(read_only=True)

    class Meta:
        model = Item
        fields = [
            'id',
            'name',
            'images',
            'price',
            'vehicle_specs',
            'price_unit',
            'price_after_discount',
            'category',
            'discount',
            'new_category_listing_type',
            'new_category',
            'new_sub_category',
            'mds_document',
            'category_type',
            'extra_fields',
            'sub_items',
            'owner_name',
            'owner_image',
            'status',
            'description',
            'longitude',
            'latitude',
            'address_line1',
            'address_line2',
            'city',
            'province',
            'zip_code',
            'country',
            'on_site_pickup',
            'quantity',
            'minimum_selling_quantity',
            'on_site_contact_phone',
            'on_site_contact_name',

        ]
        read_only_fields = ['id', 'owner_image', 'price_unit']
    def get_price_unit(self, obj):
        return obj.category.price_unit
    
    def get_owner_name(self, obj):
        return obj.owner.name

    def get_owner_image(self, obj):
        if obj.owner.image:
            if self.context.get('request'):
                return self.context.get('request').build_absolute_uri(
                    obj.owner.image.url
                )
            return obj.owner.image.url
        return None

    def get_images(self, obj):
        return obj.images.order_by('is_thumbnail')

    def to_representation(self, instance):
        data=super().to_representation(instance)
        # if hasattr(instance, 'rent_item_info') and instance.rent_item_info is None:
        #   data.pop('rent_item_info', None)
        return data
    
    def validate_sub(self, data):
        if 'category' in data:
            # print('\n we are inside the validate sub getting the extra field',data.get('extra_fields'))
            if data['category'].sub_item_type and not data.get('sub_items'):
                raise serializers.ValidationError('Sub items are required')
            if data['category'].field_types.exists():
                if not data.get('extra_fields'):
                    raise serializers.ValidationError(
                        'Extra fields are required'
                    )
                if data['category'].field_types.count() != len(
                    data['extra_fields']
                ):
                    raise serializers.ValidationError(
                        'Extra fields are not complete'
                    )
                for field in data['extra_fields']:
                    if not Category.objects.filter(
                        id=data['category'].id, field_types__name=field['name']
                    ).exists():
                        raise serializers.ValidationError(
                            'Extra field name does not belong to the category'
                        )

    
    def create(self, validated_data):
        # Validate and pop extra_fields and sub_items
        self.validate_sub(validated_data)
        extra_fields = None
        # sub_items = None
        sub_items = validated_data.pop('sub_items', [])

        if 'extra_fields' in validated_data:
            extra_fields = validated_data.pop('extra_fields')
        if 'sub_items' in validated_data:
            sub_items = validated_data.pop('sub_items')

        # Create the item
        owner = self.context['request'].user
        item = Item.objects.create(owner=owner, **validated_data)

        # Handling extra fields like make, model, model_year (if rental category)
        if extra_fields and item.category.field_types.exists():
            for field in extra_fields:
                field_name = field.pop('name')
                field_type = item.category.field_types.get(name=field_name)

                # If file type extra field (e.g. license)
                if field_type.data_type == FieldType.FILE:
                    file_val = field.get('file_value')
                    if file_val:
                        ExtraField.objects.create(item=item, type=field_type, file_value=file_val)
                    else:
                        ExtraField.objects.create(item=item, type=field_type, file_value=field.get('value'))
                else:
                    # For normal fields like make, model, model_year
                    value = field.get('value')
                    ExtraField.objects.create(item=item, type=field_type, value=value)

        # Handling sub_items (like numberPlate, images, etc.)
        if sub_items and item.category.sub_item_type:
            for sub_item in sub_items:
                files = sub_item.pop('files', [])
                temp_value = sub_item.pop('temp_value', None)
                
                # Each sub_item may have a different numberPlate or other data
                created_sub_item =SubItem.objects.create(item=item, **sub_item)
                if temp_value:
                    setattr(created_sub_item, 'temp_value', temp_value)
                for file_data in files:
                    UploadFilesSubItem.objects.create(
                        subitem=created_sub_item,
                        file=file_data.get('file'),
                        expiry_date=file_data.get('expiry_date', None)
                    )
                    # created_sub_item.files.append({"filename": file['filename'], "expiry_date": file.get('expiry_date', None)})
                    # created_sub_item.save()
                    # sub_item.save()

        return item    

class ItemSerializer(serializers.ModelSerializer):
    extra_fields = ExtraFieldSerializer(many=True, required=False)
    sub_items = SubItemSerializer(many=True, required=False)
    owner_name = serializers.SerializerMethodField()
    owner_image = serializers.SerializerMethodField()
    owner_id = serializers.SerializerMethodField()
    images = ImageSerializer(many=True, read_only=True)
    price_unit = serializers.SerializerMethodField()
    category_type = serializers.CharField(
        source='category.category_group.group_type', read_only=True
    )
    new_category_listing_type = serializers.ChoiceField(
        choices=CategoryGroup.LISTING_TYPE_CHOICES, required=False
    )
    new_category = serializers.CharField(
        max_length=100, write_only=True, required=False
    )
    new_sub_category = serializers.CharField(
        max_length=100, write_only=True, required=False
    )
    category=CategorySerializer()
    staff_note = serializers.SerializerMethodField()

    # rent_item_info = RentItemInfoSerializer(required=False)

    class Meta:
        model = Item
        fields = [
            'id',
            'name',
            'images',
            'price',
            'price_unit',
            'price_after_discount',
            'category',
            'discount',
            'new_category_listing_type',
            'new_category',
            'new_sub_category',
            'mds_document',
            'category_type',
            'extra_fields',
            'sub_items',
            'owner_name',
            'owner_image',
            'owner_id',
            'status',
            'description',
            'longitude',
            'latitude',
            'address_line1',
            'address_line2',
            'city',
            'province',
            'zip_code',
            'country',
            'on_site_pickup',
            'quantity',
            # 'rent_item_info',
            'minimum_selling_quantity',
            'on_site_contact_phone',
            'on_site_contact_name',
            'staff_note'

        ]
        read_only_fields = ['id', 'owner_image', 'price_unit']

    
    
    def get_price_unit(self, obj):
        return obj.category.price_unit
    
    def get_owner_name(self, obj):
        return obj.owner.name

    def get_owner_image(self, obj):
        if obj.owner.image:
            if self.context.get('request'):
                return self.context.get('request').build_absolute_uri(
                    obj.owner.image.url
                )
            return obj.owner.image.url
        return None
    def get_owner_id(self,obj):
        return obj.owner.id

    def get_images(self, obj):
        return obj.images.order_by('is_thumbnail')

    def get_staff_note(self, obj):
        if obj.status == Item.REJECTED:
            return obj.staff_note
        return None


    def to_representation(self, instance):
        data = super().to_representation(instance)

        

        return data
    
    def validate_sub(self, data):
        if 'category' in data:
            if data['category'].sub_item_type and not data.get('sub_items'):
                raise serializers.ValidationError('Sub items are required')
            if data['category'].field_types.exists():
                if not data.get('extra_fields'):
                    raise serializers.ValidationError(
                        'Extra fields are required'
                    )
                if data['category'].field_types.count() != len(
                    data['extra_fields']
                ):
                    raise serializers.ValidationError(
                        'Extra fields are not complete'
                    )
                for field in data['extra_fields']:
                    if not Category.objects.filter(
                        id=data['category'].id, field_types__name=field['name']
                    ).exists():
                        raise serializers.ValidationError(
                            'Extra field name does not belong to the category'
                        )

    def create(self, validated_data):

        self.validate_sub(validated_data)
        extra_fields = None
        sub_items = validated_data.pop('sub_items', [])
        # sub_items = None

        if 'extra_fields' in validated_data:
            extra_fields = validated_data.pop('extra_fields')
        if 'sub_items' in validated_data:
            sub_items = validated_data.pop('sub_items')

        owner = self.context['request'].user
        item = Item.objects.create(owner=owner, **validated_data)

        if extra_fields and item.category.field_types.exists():
            for field in extra_fields:
                name = field.pop('name')
                type = item.category.field_types.get(name=name)
                ExtraField.objects.create(
                    item=item, type=type, value=field['value']
                )

        if sub_items and item.category.sub_item_type:
            for sub_item in sub_items:
                files = sub_item.pop('files', [])
                created_sub_item =SubItem.objects.create(item=item, **sub_item)
                for file_data in files:
                    UploadFilesSubItem.objects.create(
                        subitem=created_sub_item,
                        file=file_data.get('file'),
                        expiry_date=file_data.get('expiry_date', None)
                    )
                    # created_sub_item.files.append({"filename": file['filename'],"expiry_date": file.get('expiry_date', None)})
                    # created_sub_item.save()

        return item

    def update(self, instance, validated_data):
        extra_fields = None
        # sub_items = None
        sub_items = validated_data.pop('sub_items', [])
        
        if 'extra_fields' in validated_data:
            extra_fields = validated_data.pop('extra_fields')
        if 'sub_items' in validated_data:
            sub_items = validated_data.pop('sub_items')
        if instance.category.field_types.exists() and extra_fields:
            for field in extra_fields:
                if not FieldType.objects.filter(
                    name=field['name'], categories__in=[instance.category]
                ).exists():
                    raise serializers.ValidationError(
                        'Extra field type does not belong to the category'
                    )

            del_extra_fields = instance.extra_fields.exclude(
                type__name__in=[field['name'] for field in extra_fields]
            )
            del_extra_fields.delete()

            for field in extra_fields:
                name = field.pop('name')
                type = instance.category.field_types.get(name=name)

                if ExtraField.objects.filter(
                    item=instance, type=type
                ).exists():
                    extra_field = instance.extra_fields.get(type=type)
                    extra_field.value = field['value']
                    extra_field.save()
                else:
                    ExtraField.objects.create(
                        item=instance, type=type, value=field['value']
                    )

        if instance.category.sub_item_type and sub_items:
            del_sub_items = instance.sub_items.exclude(
                value__in=[sub_item['value'] for sub_item in sub_items]
            )
            del_sub_items.delete()

            for sub_item in sub_items:
                files = sub_item.pop('files', None)
                created_sub_item, _ = SubItem.objects.get_or_create(item=instance, **sub_item)
                if files is not None:
                    UploadFilesSubItem.objects.filter(subitem=created_sub_item).delete()
                    # created_sub_item.files = []
                    for file in files:
                        UploadFilesSubItem.objects.create(
                            subitem=created_sub_item,
                            file=file.get('file'),
                            expiry_date=file.get('expiry_date', None)
                        )
                        # created_sub_item.files.append({
                        #     "filename": file['filename'],
                        #     "expiry_date": file.get('expiry_date', None)
                        #     })
                        # created_sub_item.save()
                if not SubItem.objects.filter(
                    item=instance, **sub_item
                ).exists():
                    SubItem.objects.create(item=instance, **sub_item)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.status = Item.PENDING
        instance.save()
        return instance


class FilterItemSerializer(serializers.ModelSerializer):
    category = serializers.CharField(required=False)
    type = serializers.CharField(required=False)

    class Meta:
        model = Item
        fields = ['type', 'category']

    # def validate_category(self, category):
    #     categories = Category.objects.all()
    #     for category in categories:
    #         if (
    #             category.name.lower().strip() == category.lower().strip()
    #             or category.name_ar.lower().strip() == category.lower().strip()
    #         ):
    #             raise serializers.ValidationError('Invalid category.')
    #     return category

def validate_category(self, category):
    try:
        category_obj = Category.objects.get(id=category)  
    except Category.DoesNotExist:
        raise serializers.ValidationError("Invalid category ID.")  

    categories = Category.objects.all()
    for cat in categories:  
        if (
            cat.name.lower().strip() == str(category_obj.name).lower().strip()  
            or cat.name_ar.lower().strip() == str(category_obj.name_ar).lower().strip()
        ):
            raise serializers.ValidationError('Invalid category.')
    
    return category  

class FilterUserItemSerializer(serializers.ModelSerializer):
    category_group = serializers.CharField(required=False)
    # category = serializers.CharField(required=False)
    # type = serializers.CharField(required=False)

    class Meta:
        model = Item
        fields = ['category_group']

    def validate_category_group(self, type):
        valid_types = [
            choice[0] for choice in CategoryGroup.LISTING_TYPE_CHOICES
        ]  # Extract only keys
        if type not in valid_types:
            raise serializers.ValidationError('Invalid property type.')
        return type


class ItemApproveSerializer(ItemSerializer):
    on_site_contact_name = serializers.CharField(
        required=False, allow_blank=True
    )
    on_site_contact_phone = serializers.CharField(
        required=False, allow_blank=True
    )
    category = CategorySerializer()
    class Meta:
        model = Item
        fields = ItemSerializer.Meta.fields + [
            'on_site_contact_name',
            'on_site_contact_phone',
            'status',
            'staff_note',
            'category'
        ]
        extra_kwargs = {
            'status': {'read_only': True},
            'staff_note': {'read_only': True},
        }


class ItemEditApproveSerializer(ItemSerializer):
    on_site_contact_name = serializers.CharField(
        required=False, allow_blank=True
    )
    on_site_contact_phone = serializers.CharField(
        required=False, allow_blank=True
    )
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    class Meta:
        model = Item
        fields = ItemSerializer.Meta.fields + [
            'on_site_contact_name',
            'on_site_contact_phone',
            'status',
            'staff_note',
            'category'
        ]
        extra_kwargs = {
            'status': {'read_only': True},
            'staff_note': {'read_only': True},
        }   


class UserShortSerializer(serializers.ModelSerializer):
    cr_number = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['name', 'email', 'contact_number', 'cr_number']

    def get_cr_number(self, obj):
        if hasattr(obj, 'business_profile'):
            return obj.business_profile.cr_number
        return None
    



class allAssociatedCategoriesSerializer(serializers.ModelSerializer):
    # Define a SerializerMethodField for related categories
    relatedItems = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'relatedItems']  # Fields to include in the response

    def get_relatedItems(self, obj):
        related_categories = obj.associated_categories.all()
        province = self.context.get('province')
        longitude = float(self.context.get('longitude'))
        latitude = float(self.context.get('latitude'))


        bounding_box= 70  #this is the KM of the box



        min_lat = latitude - (bounding_box / 111.32)  # 1 degree latitude ~ 111.32 km
        max_lat = latitude + (bounding_box / 111.32)
        min_lon = longitude - (bounding_box / (111.32 * math.cos(math.radians(latitude))))
        max_lon = longitude + (bounding_box / (111.32 * math.cos(math.radians(latitude))))
        items = Item.objects.filter(category__in=related_categories,province=province)

        filtered_items = items.filter(
            latitude__gte=min_lat,
            latitude__lte=max_lat,
            longitude__gte=min_lon,
            longitude__lte=max_lon
        )







        extra_filtered_items = filtered_items.filter(category__category_group__group_type='service',status=Item.APPROVED,category__status=Category.APPROVED)
        
        lab_test=extra_filtered_items.filter(category__name="Lab Test")
        unloading=extra_filtered_items.filter(category__name="Loading / Unloading")
        inspection=extra_filtered_items.filter(category__name="Inspection")
        
        return {
            "Lab Test":ItemSerializer(lab_test, many=True).data,
            "Unloading":ItemSerializer(unloading, many=True).data,
            "Inspection":ItemSerializer(inspection, many=True).data}
        
    # class RentalItemSerializer(serializers.ModelSerializer):
