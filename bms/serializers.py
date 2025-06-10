from pms.models import User
from django.utils import timezone
import datetime
from django.db.models import Q
from rest_framework import serializers
from .models import Order, OrderItem,OrderItemReport, OrderSubItem, OrderItemExtraField, OrderTracking,TrackingSystemAddresses
from inventory.models import Item, SubItem
from pms.serializers import AddressSerializer
from inventory.serializers import (
    FieldTypeSerializer,
    ImageSerializer,
    CategorySerializer,
)
from .moyasar import process_payment_card
from .utils import validate_credit_card, get_shipping_options


class OrderBuyerSerializer(serializers.ModelSerializer):
    cr_number = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["name", "email", "contact_number", "cr_number"]

    def get_cr_number(self, obj):
        if hasattr(obj, "business_profile"):
            return obj.business_profile.cr_number
        return None


class OrderItemExtraFieldSerializer(serializers.ModelSerializer):
    type = FieldTypeSerializer(read_only=True)
    name = serializers.CharField(write_only=True)

    class Meta:
        model = OrderItemExtraField
        fields = ["value", "type", "name"]


class OrderItemSubItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderSubItem
        fields = ["value"]


class OrderTrackingSerializer(serializers.ModelSerializer):
    steps = serializers.SerializerMethodField()
    require_file =serializers.SerializerMethodField()

    class Meta:
        model = OrderTracking
        fields = ["status", "steps","require_file"]

    def get_steps(self, obj):
        return obj.steps
    def get_require_file(self,obj):
        return obj.require_file
    
class TrackingSystemAddressesSerializer(serializers.ModelSerializer):
    pickup_address = AddressSerializer()
    destination_address = AddressSerializer()
    class Meta:
        model = TrackingSystemAddresses
        fields = ["pickup_address", "destination_address"]


class OrderItemSerializer(serializers.ModelSerializer):
    extra_fields = OrderItemExtraFieldSerializer(many=True, required=False)
    sub_items = OrderItemSubItemSerializer(many=True, required=False)
    images = ImageSerializer(many=True, read_only=True)
    category = CategorySerializer()
    itemID = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    owner_image = serializers.SerializerMethodField()
    tracking = OrderTrackingSerializer(read_only=True)
    tracking_system_addresses = TrackingSystemAddressesSerializer(read_only=True)
    driver_tracking = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "itemID",
            "name",
            "images",
            "price",
            "category",
            "discount",
            "mds_document",
            "extra_fields",
            "sub_items",
            "owner_name",
            "owner_image",
            "description",
            "address_line1",
            "address_line2",
            "city",
            "province",
            "zip_code",
            "country",
            "on_site_pickup",
            "quantity",
            "order_quantity",
            "total_price",
            "total_price_after_discount",
            "total_discount",
            "on_site_contact_name",
            "on_site_contact_phone",
            "tracking",
            "tracking_system_addresses",
            "driver_tracking",
        ]

    def get_itemID(self, obj):
        return obj.item.id
    
    def get_driver_tracking(self, obj):
        # نحاول الحصول على سجل التتبع المباشر المتعلق بهذا العنصر
        dt = getattr(obj, "driver_tracking", None)  # use first() لتجنب MultipleObjectsReturned
        if dt:
            return {
                "driver": dt.driver.user.name if dt.driver else None,
                "status": dt.status,
                "start_time": dt.start_time,
                "end_time": dt.end_time,
            }
        return None

    def get_owner_name(self, obj):
        return obj.owner.name

    def get_owner_image(self, obj):
        if obj.owner.image:
            if self.context.get("request"):
                return self.context.get("request").build_absolute_uri(
                    obj.owner.image.url
                )
            return obj.owner.image.url
        return None

    def validate(self, obj):
        if obj.order_quantity > obj.quantity:
            raise serializers.ValidationError("Not in stock")


class OrderBillSerializer(serializers.ModelSerializer):
    # id = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True)
    bill_type = serializers.SerializerMethodField()
    buyer = OrderBuyerSerializer()
    total_price = serializers.ReadOnlyField()
    total_discount = serializers.ReadOnlyField()
    total_price_after_discount = serializers.ReadOnlyField()
    tax_amount = serializers.ReadOnlyField()
    total_with_tax = serializers.ReadOnlyField()

    class Meta:
        model = Order
        exclude = ["status", "delivery_charges"]

    # def get_id(self, obj):
    #     return obj.id

    def get_bill_type(self, obj):
        if obj.buyer.is_business:
            return "taxinvoice"
        else:
            return "simplifiedinvoice"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    buyer = OrderBuyerSerializer()
    total_price = serializers.ReadOnlyField()
    total_discount = serializers.ReadOnlyField()
    total_price_after_discount = serializers.ReadOnlyField()
    tax_amount = serializers.ReadOnlyField()
    total_with_tax = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = "__all__"

    def get_items(self, obj):
        user = self.context["request"].user
        if obj.buyer == user:
            items = obj.order_items.all()
        else:
            items = obj.order_items.filter(owner=user)

        # Apply group_type filter if provided
        print('inside the serial',self.context["group_type"] )
        if self.context["group_type"]:
            items = items.filter(category__category_group__group_type=self.context["group_type"])
        return OrderItemSerializer(items, many=True).data
    
class OrderFilterSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    buyer = OrderBuyerSerializer()
    total_price = serializers.ReadOnlyField()
    total_discount = serializers.ReadOnlyField()
    total_price_after_discount = serializers.ReadOnlyField()
    tax_amount = serializers.ReadOnlyField()
    total_with_tax = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = "__all__"

    def get_items(self, obj):
        user = self.context["request"].user
        if obj.buyer == user:
            items = obj.order_items.all()
        else:
            items = obj.order_items.filter(owner=user)

        # Apply group_type filter if provided
        # print('inside the serial',self.context["group_type"] )
        if self.context["group_type"]:
            items = items.filter(category__category_group__group_type=self.context["group_type"])
        return OrderItemSerializer(items, many=True).data



class OrderItemChildSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    order_quantity = serializers.IntegerField()

    class Meta:
        model = OrderItem
        fields = ["item", "order_quantity"]

    def validate_order_quantity(self, order_quantity):
        if order_quantity <= 0:
            raise serializers.ValidationError("Order quantity must be positive")

    def validate(self, obj):
        print("here is ", obj["item"].name)
        print("here is ", obj["item"].quantity)
        if obj["order_quantity"] > obj["item"].quantity:
            raise serializers.ValidationError(
                {"item_quantity": f"{obj['item']} Not in stock"}
            )
        return obj


class OrderItemQuantitySerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    order_quantity = serializers.IntegerField(required=False)
    additional_services = OrderItemChildSerializer(many=True, required=False)
    parent_order_item = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(), required=False
    )

    class Meta:
        model = OrderItem
        fields = ["item", "order_quantity", "additional_services", "parent_order_item"]

    def validate(self, obj):
        
        item = obj["item"]
        try:
            Item.objects.get(id=item.id)
        except Item.DoesNotExist():
            raise serializers.ValidationError({"item": f"{obj['item']} does not exist"})
        item_quantity = obj.get("item").quantity
        order_quantity = obj.get("order_quantity")
        if order_quantity is not None:
            if order_quantity <= 0:
                raise serializers.ValidationError("Order quantity must be positive")
            if order_quantity > item_quantity:
                raise serializers.ValidationError(
                    {"item_quantity": f"{obj['item']} Not in stock"}
                )
    
        return obj


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemQuantitySerializer(many=True)
    shipping_option = serializers.IntegerField()
    name = serializers.CharField(max_length=50)
    number = serializers.CharField(max_length=16)
    month = serializers.CharField(max_length=2)
    year = serializers.CharField(max_length=4)
    cvc = serializers.CharField(max_length=3)
    save = serializers.BooleanField(default=False)

    class Meta:
        model = Order
        exclude = [
            "buyer",
            "delivery_charges",
            "zatca_qr",
            "base64_invoice",
            "invoice_hash",
            "payment_id",
            "payment_date",
        ]

    def validate_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Card number must be digits only")
        if len(value) != 16:
            raise serializers.ValidationError("Card number must be 16 digits")
        if not validate_credit_card(value):
            raise serializers.ValidationError("Invalid card number")
        return value

    def validate_month(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Month must be digits only")
        if not 1 <= int(value) <= 12:
            raise serializers.ValidationError("Invalid month")
        return value

    def validate_year(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Year must be digits only")
        if len(value) != 4:
            raise serializers.ValidationError("Year must be 4 digits")
        if int(value) < timezone.now().year:
            raise serializers.ValidationError("Invalid year")
        return value

    def validate_cvc(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("CVC must be digits only")
        if len(value) != 3:
            raise serializers.ValidationError("CVC must be 3 digits")
        return value

    def validate_shipping_option(self, value):
        shipping_options = get_shipping_options() 
        if value not in [option["id"] for option in shipping_options]:
            raise serializers.ValidationError("Invalid shipping option")
        return value

    def validate(self, data):
        month = int(data.get("month"))
        year = int(data.get("year"))
        if year < timezone.now().year or (
            year == timezone.now().year and month < timezone.now().month
        ):
            raise serializers.ValidationError("Card has expired")
        return data

    def create(self, validated_data):
        # print("validated_data", validated_data)
        user = self.context["request"].user
        items = validated_data.pop("items")

        name = validated_data.pop("name")
        number = validated_data.pop("number")
        month = validated_data.pop("month")
        year = validated_data.pop("year")
        cvc = validated_data.pop("cvc")
        save = validated_data.pop("save")

        shipping_option = validated_data.pop("shipping_option")
        shipping_options = get_shipping_options()
        selected_delivery_option = [
            i for i in shipping_options if i["id"] == shipping_option
        ][0]

        if user.is_authenticated:
            order = Order.objects.create(
                buyer=user,
                delivery_charges=selected_delivery_option["price"],
                shipping_option=shipping_option,
                **validated_data,
            )
        else:
            order = Order.objects.create(
                buyer_email=user.email,
                delivery_charges=selected_delivery_option["price"],
                shipping_option=shipping_option,
                **validated_data,
            )

        for item in items:
            real_item = Item.objects.get(pk=item["item"].id)

            if "order_quantity" in item:
                real_item.quantity = real_item.quantity - item["order_quantity"]
            else:
                item["order_quantity"] = 1
                real_item.quantity = 1
            print("before parent order check", item)
            parent_order_item = None
            if "parent_order_item" in item:
                parent_item_instance = Item.objects.get(pk=item["parent_order_item"].id)
                parent_order_item_instance = OrderItem.objects.get(
                    item=parent_item_instance, order=order
                )
                parent_order_item = parent_order_item_instance
            print("before creating an item", item)
            order_item = OrderItem.objects.create(
                item=real_item,
                name=real_item.name,
                description=real_item.description,
                price=real_item.price,
                discount=real_item.discount,
                address_line1=real_item.address_line1,
                address_line2=real_item.address_line2,
                city=real_item.city,
                province=real_item.province,
                zip_code=real_item.zip_code,
                country=real_item.country,
                on_site_contact_name=real_item.on_site_contact_name,
                on_site_contact_phone=real_item.on_site_contact_phone,
                on_site_pickup=real_item.on_site_pickup,
                category=real_item.category,
                quantity=real_item.quantity,
                order_quantity=item["order_quantity"],
                mds_document=real_item.mds_document,
                owner=real_item.owner,
                staff_note=real_item.staff_note,
                order=order,
                parent_order_item=parent_order_item,
            )
            real_item.save()

            if real_item.extra_fields:
                for field in real_item.extra_fields:
                    OrderItemExtraField.objects.create(
                        order_item=order_item,
                        type=field.type,
                        value=field.value,
                    )

            sub_items = SubItem.objects.filter(item=real_item)
            if sub_items.exists():
                for sub_item in sub_items:
                    value = sub_item.value
                    OrderSubItem.objects.create(item=order_item, value=value)

            additional_services = item.get("additional_services", [])
            for subi in additional_services:
                real_subi = Item.objects.get(pk=subi["item"].id)
                real_subi.quantity = real_subi.quantity - subi["order_quantity"]
                order_subi = OrderItem.objects.create(
                    item=real_subi,
                    name=real_subi.name,
                    description=real_subi.description,
                    price=real_subi.price,
                    discount=real_subi.discount,
                    address_line1=real_subi.address_line1,
                    address_line2=real_subi.address_line2,
                    city=real_subi.city,
                    province=real_subi.province,
                    zip_code=real_subi.zip_code,
                    country=real_subi.country,
                    on_site_contact_name=real_subi.on_site_contact_name,
                    on_site_contact_phone=real_subi.on_site_contact_phone,
                    on_site_pickup=real_subi.on_site_pickup,
                    category=real_subi.category,
                    quantity=real_subi.quantity,
                    order_quantity=subi["order_quantity"],
                    mds_document=real_subi.mds_document,
                    owner=real_subi.owner,
                    staff_note=real_subi.staff_note,
                    order=order,
                    parent_order_item=order_item,
                )
                real_subi.save()

                if real_subi.extra_fields:
                    for field in real_subi.extra_fields:
                        OrderItemExtraField.objects.create(
                            order_item=order_subi,
                            type=field.type,
                            value=field.value,
                        )

                sub_subis = SubItem.objects.filter(item=real_subi)
                if sub_subis.exists():
                    for sub_subi in sub_subis:
                        value = sub_subi.value
                        OrderSubItem.objects.create(item=order_subi, value=value)

        amount = order.total_price_after_discount
        amount_x100 = amount * 100

        # process payment
        payment_response = process_payment_card(
            amount=amount_x100.to_integral(),
            name=name,
            number=number,
            month=month,
            year=year,
            cvc=cvc,
            save_card=save,
        )

        order.payment_id = payment_response["id"]
        order.save()

        return order, payment_response["source"]["transaction_url"]


class FilterOrderSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Order.STATUS, required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    class Meta:
        model = Order
        fields = [
            "status",
            "start_date",
            "end_date",
        ]

    def validate_status(self, status):
        if status not in [key for key, value in Order.STATUS]:
            raise serializers.ValidationError({"error": "Invalid order status"})
        return status

    def validate_start_date(self, start_date):
        if start_date > timezone.now().date():
            raise serializers.ValidationError(
                "Start date should be less than current date"
            )
        return start_date

    def validate_end_date(self, end_date):
        if self.initial_data.get("start_date"):
            if (
                end_date
                < datetime.datetime.strptime(
                    self.initial_data["start_date"], "%Y-%m-%d"
                ).date()
            ):
                raise serializers.ValidationError(
                    "End date should be greater than start date"
                )
        return end_date


class DisposalCertificateSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    contact_number = serializers.SerializerMethodField()
    treatment = serializers.SerializerMethodField()
    material = serializers.SerializerMethodField()
    weight = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "created_at",
            "id",
            "location",
            "contact_number",
            "name",
            "treatment",
            "material",
            "weight",
            "type",
        ]
    def get_type(self, obj):
        return 'json'
    def get_created_at(self, obj):
        return obj.order.created_at

    def get_location(self, obj):
        return obj.address_line1 + ", " + obj.city + ", " + obj.province

    def get_contact_number(self, obj):
        return obj.on_site_contact_phone

    def get_treatment(self, obj):
        if (
            obj.name == "paper recycling"
            or obj.name == "plastic recycling"
            or obj.name == "glass recycling"
            or obj.name == "metal recycling"
        ):
            return "recycling"
        if (
            obj.name == "paper disposal"
            or obj.name == "plastic disposal"
            or obj.name == "glass disposal"
            or obj.name == "metal disposal"
        ):
            return "disposal"

    def get_weight(self, obj):
        return obj.order_quantity

    def get_material(self, obj):
        if obj.name == "paper recycling":
            return "paper"
        if obj.name == "plastic recycling":
            return "plastic"
        if obj.name == "glass recycling":
            return "glass"
        if obj.name == "metal recycling":
            return "metal"
        else:
            return "other"
        
    
class OrderItemReportSerializer(serializers.ModelSerializer):
    report = serializers.FileField()
    order_item = serializers.PrimaryKeyRelatedField(queryset=OrderItem.objects.all())
    type= serializers.SerializerMethodField()

    class Meta:
        model = OrderItemReport
        fields = ["report", "order_item","type"]

    def get_type(self, obj):
        return 'file'
    
    def validate_report(self, report):
        if report.size > 10485760:
            raise serializers.ValidationError("File size should be less than 10MB")
        return report
    
class OrderContractsSerializer(serializers.ModelSerializer):
    contract = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    type= serializers.SerializerMethodField()
    class Meta:
        model = OrderItem
        fields = ["contract","created_at","type"]
        
    def get_type(self, obj):
        return 'markdown'
    
    def get_contract(self, obj):
        print(self.context.get("request"))
        user=self.context.get("request")
        contract = obj.category.contract_text or ""
        seller_info = f"**إسم البائع:** {obj.owner.name}\n\n**بريد البائع:** {obj.owner.email}"
        buyer_info = f"**إسم المشتري:** {user.name}\n\n**بريد المشتري:** {user.email}"
        selling_date = f"**تاريخ الشراء:** {obj.order.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        contract_with_info = f"{seller_info}\n\n{buyer_info}\n\n{selling_date}"
        seperator="\n\n"+"-"*50+"\n\n"
        contract_full = contract_with_info+"\n\n"+seperator +  "\n\n"+ contract
        return contract_full
    
    def get_created_at(self, obj):
        return obj.order.created_at
