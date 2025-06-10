import uuid
import os
from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework import status

def get_field_type_icon_path(instance, filename):
    filename = instance.name + '.' + filename.split('.')[-1]
    return f'field_type_icons/{filename}'

def mds_upload_path(instance, filename):
    # Exemple simple de path de fichier
    return f"uploads/{instance.owner.name}/{filename}"


def get_categorygroup_icon_path(instance, filename):
    filename = instance.name + '.' + filename.split('.')[-1]
    return f'categorygroup_icons/{filename}'

def get_item_image_path(instance, filename):
    filename = str(uuid.uuid4()) + '.' + filename.split('.')[-1]
    return f'item_images/{filename}'

class DummyOwner:
    name = "TestCompany"

class DummyInstance:
    owner = DummyOwner()

print(mds_upload_path(DummyInstance(), "test_file.csv"))



def rental_documents_upload_path(instance, filename):
   
    base_filename, file_extension = os.path.splitext(filename)
    timestamp = now().strftime("%Y%m%d%H%M%S")
    
    
    return f"sub_item_files/{instance.id}_{timestamp}{file_extension}"


def get_item_document_path(instance, filename):
    return f'company_docs/{instance.item.owner.name}/item_documents/{filename}'


def get_item_document_path(instance, filename):
    return f'company_docs/{instance.item.owner.name}/item_documents/{filename}'


def handle_vehicle_specs(item_data, category_obj):
    
   
    from inventory.models import VehicleSpecs
    vehicle_specs_obj = None
    make = item_data.get("make")
    model = item_data.get("model")
    model_year = item_data.get("model_year")

    if not any([make, model, model_year]):
        return None  

  

    if not any([make, model, model_year]):
        return None
        

    # معالجة القيم إذا كان المستخدم اختار "Other"
    if make == "Other":
        make = item_data.get("make_value")
        if not make:
            return Response(
                {"error": "يجب إدخال قيمة make عند اختيار Other"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if model == "Other":
        model = item_data.get("model_value")
        if not model:
            return Response(
                {"error": "يجب إدخال قيمة model عند اختيار Other"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if model_year == "Other":
        model_year = item_data.get("model_year_value")
        if not model_year:
            return Response(
                {"error": "يجب إدخال قيمة model_year عند اختيار Other"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # التحقق من أن جميع الحقول موجودة
    if not all([make, model, model_year]):
        return Response(
            {"error": "جميع الحقول (make, model, model_year) مطلوبة عند إدخال vehicle_specs"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # البحث عن VehicleSpecs المطابقة
    vehicle_spec = category_obj.vehicle_specs.filter(
        make=make,
        model=model,
        model_year=model_year
    ).first()

    # إذا لم يتم العثور عليها، نقوم بإنشائها
    if not vehicle_spec:
        vehicle_spec = VehicleSpecs.objects.create(
            make=make,
            model=model,
            model_year=model_year,
            categories=category_obj,
            status="pending"
        )
        print(f"✅ VehicleSpecs جديدة أُنشئت وربطت بالكاتيجوري: {vehicle_spec}")

    return vehicle_spec