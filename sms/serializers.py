from rest_framework import serializers
from django.conf import settings
from django.apps import apps
from django.contrib.auth import get_user_model

from sms.models import ScrapItem, ScrapImage, BankingInfo, OrderScrap
from inventory.models import Category, CategoryGroup


User = get_user_model()

class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'contact_number', 'pickup_address', 'user_type']


class ScrapImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapImage
        fields = ['image']


class BankingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankingInfo
        fields = ['full_name', 'bank_name', 'iban_number']


class ScrapItemSerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.ImageField(), write_only=True)
    banking_info = BankingInfoSerializer(write_only=True)
    email = serializers.EmailField(write_only=True)
    user_type = serializers.ChoiceField(
        choices=["individual", "business", "driver", "admin", "staff"],
        write_only=True
    )
    pickup_address = serializers.CharField(
        max_length=255, write_only=True, required=False, allow_blank=True
    )
    phone = serializers.CharField(
        max_length=20, write_only=True, required=False, allow_blank=True
    )

    class Meta:
        model = ScrapItem
        fields = [
            'id', 'email', 'user_type', 'pickup_address', 'phone',
            'category_group', 'banking_info', 'name', 'size', 'quantity',
            'description', 'status', 'images', 'total_amount',
        ]

    def create(self, validated_data):
        app_label, model_name = settings.AUTH_USER_MODEL.split('.')
        User = apps.get_model(app_label, model_name)

        email = validated_data.pop('email')
        user_type = validated_data.pop('user_type')
        pickup_address = validated_data.pop('pickup_address', '')
        phone = validated_data.pop('phone', None)
        banking_data = validated_data.pop('banking_info')
        images_data = validated_data.pop('images')
        total_amount = validated_data.pop('total_amount', 0)

        user = User.objects.filter(email=email).first()
        if not user:
            if phone and User.objects.filter(contact_number=phone).exclude(email=email).exists():
                raise serializers.ValidationError({
                    'phone': 'Ce numéro de téléphone est déjà utilisé par un autre utilisateur.'
                })
            user = User.objects.create(
                email=email,
                name=email.split('@')[0],
                user_type=user_type,
                contact_number=phone,
                pickup_address=pickup_address
            )
        else:
            updated = False
            if not getattr(user, 'contact_number', None) and phone:
                user.contact_number = phone
                updated = True
            if not getattr(user, 'user_type', None):
                user.user_type = user_type
                updated = True
            if not getattr(user, 'pickup_address', None) and pickup_address:
                user.pickup_address = pickup_address
                updated = True
            if updated:
                user.save()

        banking_info = BankingInfo.objects.create(
            user=user,
            full_name=banking_data.get('full_name', ''),
            bank_name=banking_data.get('bank_name', ''),
            iban_number=banking_data.get('iban_number', ''),
        )

        order = OrderScrap.objects.filter(user=user, pickup_address=pickup_address).order_by('-id').first()
        if not order:
            order = OrderScrap.objects.create(
                user=user,
                pickup_address=pickup_address,
                total_items=0,
                total_amount=total_amount
            )

        scrap_item = ScrapItem.objects.create(
            user=user,
            banking_info=banking_info,
            order=order,
            category_group=validated_data.get('category_group'),
            name=validated_data.get('name', ''),
            size=validated_data.get('size', ''),
            quantity=validated_data.get('quantity', 0),
            description=validated_data.get('description', ''),
            status=validated_data.get('status', 'pending'),
        )
        

        for image in images_data:
            ScrapImage.objects.create(scrap_item=scrap_item, image=image)

        order.total_items = order.scrap_items.count()
        order.save()

        return scrap_item



class BankingInfoReadSerializer(serializers.ModelSerializer):
    """
    Sérialiseur “lecture” pour BankingInfo (si jamais vous avez besoin
    d’afficher les infos bancaires dans une réponse GET).
    """
    class Meta:
        model = BankingInfo
        fields = ['full_name', 'bank_name', 'iban_number']


class CategoryGroupSerializer(serializers.ModelSerializer):
    """
    Sérialiseur lecture pour Category (ou CategoryGroup).
    """
    class Meta:
        model = Category
        fields = ['id', 'name']


class ScrapItemReadSerializer(serializers.ModelSerializer):
    banking_info = BankingInfoSerializer(read_only=True)  # Afficher les infos bancaires liées
    images = ScrapImageSerializer(many=True, read_only=True)  # Afficher les images liées à chaque ScrapItem
    category_group = CategoryGroupSerializer(read_only=True)  # Afficher la catégorie

    class Meta:
        model = ScrapItem
        fields = [
            'id',
            'name',
            'size',
            'quantity',
            'description',
            'status',
            'banking_info',
            'category_group',
            'images',
        ]
class OrderScrapReadSerializer(serializers.ModelSerializer):
    scrap_items = ScrapItemReadSerializer(many=True, read_only=True)
    user = UserReadSerializer(read_only=True)  
    class Meta:
        model = OrderScrap
        fields = [
            'id',
            'user',
            'pickup_address',
            'total_items',
            'scrap_items',
            'total_amount',
            'status',
            'created_at'
        ]
