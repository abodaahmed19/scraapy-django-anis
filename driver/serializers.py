from rest_framework import serializers
from .models import DriverProfile
from pms.models import User
import random
from pms.serializers import UserSerializer
from bms.models import OrderItem
from bms.serializers import OrderTrackingSerializer,OrderItemExtraFieldSerializer, TrackingSystemAddressesSerializer
from inventory.serializers import CategorySerializer,ImageSerializer

class DriverProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    contact_number = serializers.CharField(write_only=True)
    
    class Meta:
        model = DriverProfile
        exclude = ["user", "employer", "status"]
        extra_kwargs = {
            'driver_id_file': {'required': True},
            'license_file': {'required': True},
            'vehicle_registration_file': {'required': True},
            'insurance_file': {'required': True},
        }
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value
    
    def create(self, validated_data):
        request = self.context.get("request")
        employer = request.user if request and hasattr(request.user, 'business_profile') else None
        
        name = validated_data.pop("name")
        email = validated_data.pop("email")
        contact_number = validated_data.pop("contact_number")
        
        random_passowrd = str(random.randint(100000, 999999))

        
        user = User.objects.create_user(
            email=email,
            name=name,
            contact_number=contact_number,
            user_type="driver",
            password=random_passowrd,
            is_active=True
        )
        
        driver_profile = DriverProfile.objects.create(
            user=user,
            employer=employer,
            **validated_data,
        )
        
        driver_profile._generated_password = random_passowrd
        driver_profile.generated_password = random_passowrd
        return driver_profile

class DriverProfileGetSerializer(serializers.ModelSerializer):
    employer = UserSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    email = serializers.EmailField(source='user.email')
    contact_number = serializers.CharField(source='user.contact_number')
    
    class Meta:
        model = DriverProfile
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    tracking = OrderTrackingSerializer(read_only=True)
    tracking_system_addresses = TrackingSystemAddressesSerializer(read_only=True)
    images = ImageSerializer(many=True, read_only=True)
    owner_name = serializers.SerializerMethodField()
    owner_image = serializers.SerializerMethodField()
    category = CategorySerializer()
    extra_fields = OrderItemExtraFieldSerializer(many=True, required=False)


    class Meta:
        model = OrderItem
        fields = [
            'id',
            'tracking',
            'tracking_system_addresses',
            'name',
            'images',
            'description',
            'order_quantity',
            'owner_name',
            'owner_image',
            'category',
            'extra_fields',
            'order'
        ]

    def get_owner_name(self, obj):
        return obj.owner.name if obj.owner else None

    def get_owner_image(self, obj):
        if not obj.owner or not obj.owner.image:
            return None
            
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.owner.image.url)
        return obj.owner.image.url
