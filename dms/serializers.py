from rest_framework import serializers
from .models import Document, UserDocuments
from bms.serializers import OrderItemSerializer, OrderItemReportSerializer,OrderContractsSerializer,OrderItemReportSerializer,DisposalCertificateSerializer
from bms.models import OrderItem
from django.utils import timezone
import datetime

class DocumentSerializer(serializers.ModelSerializer):
    order_item = OrderItemSerializer()
    class Meta:
        model = Document
        fields = '__all__'

class DocumentCreateSerializer(serializers.ModelSerializer):
    order_item = serializers.PrimaryKeyRelatedField(queryset=OrderItem.objects.all() , error_messages={"does_not_exist": "Order item does not exist.",})
    class Meta:
        model = Document
        exclude = ['id' , 'uploaded_at']

    def validate_order_item(self, order_item):
        try:
            item = OrderItem.objects.get(pk=order_item.id)
        except OrderItem.DoesNotExist():
            raise serializers.ValidationError('No order item found')
        return item
    
class FilterDocumentSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=Document.DOCUMENT_TYPES, required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    class Meta:
        model = Document
        fields = [
            'type',
            'start_date',
            'end_date',
        ]

    def validate_status(self, status):
        if type not in [key for key, value in Document.STATUS]:
            raise serializers.ValidationError(
                {'error': 'Invalid document type'}
            )
        return status

    def validate_start_date(self, start_date):
        if start_date > timezone.now().date():
            raise serializers.ValidationError(
                'Start date should be less than current date'
            )
        return start_date

    def validate_end_date(self, end_date):
        if self.initial_data.get('start_date'):
            if (
                end_date
                < datetime.datetime.strptime(
                    self.initial_data['start_date'], '%Y-%m-%d'
                ).date()
            ):
                raise serializers.ValidationError(
                    'End date should be greater than start date'
                )
        return end_date


class UserDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDocuments
        fields = '__all__'
    def to_representation(self, instance):
        response = super().to_representation(instance)


        
        if instance.type == UserDocuments.JSON:
            response["data"] = DisposalCertificateSerializer(instance.order_item).data
            response['id'] = f"Cert-{response['id']}"
            
        elif instance.type == UserDocuments.MARKDOWN:
            response["data"] = OrderContractsSerializer(instance.order_item,context ={"request": self.context.get("request")} ).data
            response['id'] = f"Contr-{response['id']}"
        elif instance.type == UserDocuments.FILE:
            response['data'] = OrderItemReportSerializer(instance.order_item_report).data
            response['id'] = f"Service-{response['id']}"
            
        response['order_item'] = OrderItemSerializer(instance.order_item).data
        response['created_by'] = instance.order_item.owner.name
        # if instance.type == UserDocuments.FILE:
        #     response['file'] = instance.file.url
        return response

    
class FilterUserDocumentSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=UserDocuments.DOCUMENT_TYPES, required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    class Meta:
        model = Document
        fields = [
            'type',
            'start_date',
            'end_date',
        ]

    def validate_status(self, status):
        if type not in [key for key, value in UserDocuments.DOCUMENT_TYPES]:
            raise serializers.ValidationError(
                {'error': 'Invalid document type'}
            )
        return status

    def validate_start_date(self, start_date):
        if start_date > timezone.now().date():
            raise serializers.ValidationError(
                'Start date should be less than current date'
            )
        return start_date

    def validate_end_date(self, end_date):
        if self.initial_data.get('start_date'):
            if (
                end_date
                < datetime.datetime.strptime(
                    self.initial_data['start_date'], '%Y-%m-%d'
                ).date()
            ):
                raise serializers.ValidationError(
                    'End date should be greater than start date'
                )
        return end_date