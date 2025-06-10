import json
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from inventory.utils import handle_vehicle_specs
from django.shortcuts import get_object_or_404

from rest_framework import status
from django.db.models import Q
from scraapy import permissions
from scraapy.permissions import IsBusinessComplete, IsStaff
from pms.serializers import StaffVendorSerializer
from .serializers import (
    ItemSerializer,
    PostItemSerializer,
    ItemApproveSerializer,
    CategoryGroupSerializer,
    ImageSerializer,
    FilterItemSerializer,
    FilterUserItemSerializer,
    CategorySerializer,
    CategoryGroupFilteringSerializer,
    CertificateTypeSerializer,
    UploadFilesSubItemSerializer,
    VehicleSpecsSerializer,
    ApprovedCategoryGroupSerializer,
    ItemEditApproveSerializer
)
from .models import Item, CategoryGroup, Image, FieldType, Category, SubItem, UploadImagesSubItems, VehicleSpecs, CertificateType
from pms.models import User, BusinessProfile
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from external.pythonlibrary.api_responses.die import Response
from external.pythonlibrary.api_responses.error_types import ErrorTypes
from bms.models import OrderItem
from django.db.models import Sum, Case, When, IntegerField

include_search_fields = ["Location"]


class CategoryGroupListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        type = request.query_params.get("type", CategoryGroup.PRODUCT)
        category_groups = CategoryGroup.objects.filter(group_type=type,status=CategoryGroup.APPROVED)
        serializer = ApprovedCategoryGroupSerializer(
            category_groups, many=True, context={"request": request}
        )
        return Response(
            message="Categories fetched successfully",
            data=serializer.data,
            status=status.HTTP_200_OK,
        )


class CategoryGroupDetailView(APIView):
    permission_classes = [AllowAny]

    # def get(self, request, pk):
    #     try:
    #         category_group = CategoryGroup.objects.get(id=pk)
    #     except CategoryGroup.DoesNotExist:
    #         return Response(message="Not found", errors={'type': ErrorTypes.NOT_FOUND,'message': 'Category group not found'}, status=status.HTTP_404_NOT_FOUND)
    #     serializer = CategoryGroupSerializer(category_group, context={'request': request})
    #     return Response(message="Category group fetched successfully", data=serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        if (
            not request.user.business_profile.status
            == request.user.business_profile.APPROVED
        ):
            return Response(
                {"error": "Your business profile is not approved"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            category_group = CategoryGroup.objects.get(id=pk)
        except CategoryGroup.DoesNotExist:
            return Response(
                message="Not found",
                errors={
                    "type": ErrorTypes.NOT_FOUND,
                    "message": "Category group not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CategoryGroupSerializer(
            category_group,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if not serializer.is_valid():
            return Response(
                message="Validation error",
                errors=serializer.errors,
                serializer=True,
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(
            message="Category group updated successfully",
            data=serializer.data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            category_group = CategoryGroup.objects.get(id=pk)
        except CategoryGroup.DoesNotExist:
            return Response(
                {"error": "Category group not found"}, status=status.HTTP_404_NOT_FOUND
            )
        category_group.delete()
        return Response(
            message="Category group deleted successfully", status=status.HTTP_200_OK
        )


class HomeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        category_groups_product = CategoryGroup.objects.filter(group_type=CategoryGroup.PRODUCT, status=CategoryGroup.APPROVED)
        category_groups_rental = CategoryGroup.objects.filter(group_type=CategoryGroup.RENTAL, status=CategoryGroup.APPROVED)
        category_groups_service = CategoryGroup.objects.filter(group_type=CategoryGroup.SERVICE, status=CategoryGroup.APPROVED)

        best_selling_items = Item.objects.filter(status=Item.APPROVED)[:10]
        best_selling_serializer = ItemSerializer(
            best_selling_items, many=True, context={"request": request}
        )

        scraapy_items = Item.objects.filter(status=Item.APPROVED)[:10]
        scraapy_serializer = ItemSerializer(
            scraapy_items, many=True, context={"request": request}
        )

        data = {
                "categories": {
                    "product": CategoryGroupFilteringSerializer(category_groups_product, many=True, context={"request": request}).data,
                    "rental": CategoryGroupFilteringSerializer(category_groups_rental, many=True, context={"request": request}).data,
                    "service": CategoryGroupFilteringSerializer(category_groups_service, many=True, context={"request": request}).data,
                },
                "best_selling": best_selling_serializer.data,
                "scraapy": scraapy_serializer.data,
            }

        return Response(
            message="Home data fetched successfully",
            data=data,
            status=status.HTTP_200_OK,
        )

class ItemFilterView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        data = {}

        # === TRI (Sort Options) ===
        data['sort'] = {
            'label': 'Sort By',
            'options': [
                {'value': 'relavance', 'label': 'Relavance', 'label_ar': 'الصلة'},
                {'value': 'price_asc', 'label': 'Price: Low to High', 'label_ar': 'السعر من الأقل للأعلى'},
                {'value': 'price_desc', 'label': 'Price: High to Low', 'label_ar': 'السعر من الأعلى للأقل'},
                {'value': 'most_sold', 'label': 'Most Sold', 'label_ar': 'الأكثر مبيعاً'}
            ]
        }

        # === FILTRES ===
        filters = {}

        # --- Type Filter ---
        group_choices = CategoryGroup.LISTING_TYPE_CHOICES
        group_choices_ar = CategoryGroup.LISTING_TYPE_CHOICES_AR
        filters['type'] = {
            "label": "Type",
            "label_ar": "النوع",
            "options": [
                {"value": group[0], "label": group[1], "label_ar": group_choices_ar[index][1]}
                for index, group in enumerate(group_choices)
            ],
        }

        # --- Category Group Filter ---
        filters["categoryGroup"] = {
            "label": "Category",
            "label_ar": "الفئة",
            "options": [
                {
                    "value": group.id,
                    "label": group.name,
                    "label_ar": group.name_ar,
                    "type": group.group_type,
                }
                for group in CategoryGroup.objects.all()
            ],
        }

        # --- Sub Category Filter ---
        filters["category"] = {
            "label": "Sub Category",
            "label_ar": "الفئة الفرعية",
            "options": [
                {
                    "value": category.id,
                    "label": category.name,
                    "label_ar": category.name_ar,
                    "type": category.category_group.group_type,
                    "category_group": category.category_group.id,
                }
                for category in Category.objects.all()
            ],
        }

        # Ajouter d'autres filtres dynamiques si nécessaire
        include_search_fields = ['material', 'color', 'condition']  # Exemple de champs à inclure
        field_types = FieldType.objects.all()

        for field in field_types:
            if field.name in include_search_fields and field.extra_fields.count() > 0:
                label = field.name.replace("_", " ").title()
                clean_field_options = [
                    {"value": field_value.value, "label": field_value.value}
                    for field_value in field.extra_fields.filter(
                        item__status=Item.APPROVED
                    ).distinct("value")
                ]
                filters[field.name] = {"label": label, "options": clean_field_options}

        data["filters"] = filters

        # === RETOURNER LES ITEMS SI FILTRE ACTIF ===
        category_id = request.query_params.get('category')
        category_group_id = request.query_params.get('categoryGroup')

        items = Item.objects.filter(status=Item.APPROVED)

        if category_id:
            items = items.filter(category_id=category_id)
        elif category_group_id:
            items = items.filter(category__category_group_id=category_group_id)

        # Si des items sont trouvés, les ajouter aux données retournées
        if items.exists():
            data['items'] = ItemSerializer(items, many=True).data
        else:
            data['items'] = []
            data['message'] = 'Aucun item trouvé pour ces critères.'

        return Response(data, status=status.HTTP_200_OK)


class ItemListView(ListAPIView):
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination
    serializer_class = ItemSerializer

    def get_queryset(self):
        query = Item.objects.filter(status=Item.APPROVED)

        category_group_ids = self.request.query_params.get('categoryGroup')
        if category_group_ids:
            try:
                category_group_ids = [int(id.strip()) for id in category_group_ids.split(',')]
                categories = Category.objects.filter(category_group_id__in=category_group_ids)
                if categories.exists():
                    query = query.filter(category__in=categories)
                else:
                    return Item.objects.none()
            except ValueError:
                return Item.objects.none()

        category_ids = self.request.query_params.get('category')
        if category_ids:
            try:
                category_ids = [int(id.strip()) for id in category_ids.split(',')]
                categories = Category.objects.filter(id__in=category_ids)
                if categories.exists():
                    query = query.filter(category__in=categories)
                else:
                    return Item.objects.none()
            except ValueError:
                return Item.objects.none()

        sort = self.request.query_params.get('sort')
        if sort == "price_asc":
            query = query.order_by("price")
        elif sort == "price_desc":
            query = query.order_by("-price")
        elif sort == "most_sold":
            query = query.annotate(total_sold=Sum("order_item__order_quantity")).order_by("-total_sold")

        return query

    def get(self, request):
        queryset = self.get_queryset()
        filterSerializer = FilterItemSerializer(data=request.GET)
        if not filterSerializer.is_valid():
            return Response(
                message="Validation error",
                errors=filterSerializer.errors,
                serializer=True,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # if request.GET.get('type'):
        #     queryset = queryset.filter(Q(category__category_group__group_type=request.GET.get('type')))
        # if request.GET.get('category'):
        #     queryset = queryset.filter(category=request.GET.get('category'))
        if request.GET.get("seller"):
            queryset = queryset.filter(owner__name=request.GET.get("seller"))
        if request.GET.get("query"):
            query = request.GET.get("query").lower().strip()
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(owner__name__icontains=query)
                | Q(category__name__icontains=query)
                | Q(category__category_group__name__icontains=query)
            )

        if request.GET.get("type"):
            type_values = request.GET.get("type").split(
                ","
            )  # ✅ تقسيم القيم بناءً على الفاصلة
            queryset = queryset.filter(
                Q(category__category_group__group_type__in=type_values)
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(
                page, many=True, context=self.get_serializer_context()
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(
            queryset, many=True, context=self.get_serializer_context()
        )
        return Response(
            message="Items fetched successfully",
            data=serializer.data,
            status=status.HTTP_200_OK,
        )


class ItemDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            item = Item.objects.get(id=pk)
        except Item.DoesNotExist:
            return Response(
                message="Not found",
                errors={"type": ErrorTypes.NOT_FOUND, "message": "Item not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ItemSerializer(item, context={"request": request})
        return Response(
            message="Item fetched successfully",
            data=serializer.data,
            status=status.HTTP_200_OK,
        )


class UserItemListView(ListAPIView):
    permission_classes = [IsBusinessComplete]
    pagination_class = PageNumberPagination
    serializer_class = ItemSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        query = Item.objects.filter(owner=self.request.user)
        return query

    def get(self, request):
        queryset = self.get_queryset()
        filterSerializer = FilterUserItemSerializer(data=request.GET)
        if not filterSerializer.is_valid():
            return Response(
                message="Validation error",
                errors=filterSerializer.errors,
                serializer=True,
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.GET.get("category_group"):
            queryset = queryset.filter(
                category__category_group__group_type=request.GET.get("category_group")
            )
        if request.GET.get("query"):
            query = request.GET.get("query").lower().strip()
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(owner__name__icontains=query)
                | Q(category__name__icontains=query)
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(
                page, many=True, context=self.get_serializer_context()
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(
            queryset, many=True, context=self.get_serializer_context()
        )
        return Response(
            message="Items fetched successfully",
            data=serializer.data,
            status=status.HTTP_200_OK,
        )
        
    def post(self, request):
        print("Entering the post of creating a new item with category:", request.data[0])

        category = request.data[0].get("category")
        category_group = request.data[0].get("category_group")
        category_type = request.data[0].get("category_type")

        print("Category:", category)
        print("Category Group:", category_group)
        print("Category Type:", category_type)

        if isinstance(category_group, str):
            print("Creating category group")
            category_group_obj, created = CategoryGroup.objects.get_or_create(
                name=category_group,
                group_type=category_type,
                status=CategoryGroup.PENDING,
            )
            print(f"Category group created: {category_group_obj.name}")

        elif isinstance(category_group, int):
            category_group_obj = CategoryGroup.objects.get(id=category_group)
            print(f"Category group exists: {category_group_obj.name}")

        if isinstance(category, str):
            category_obj, created = Category.objects.get_or_create(
                name=category,
                category_group=category_group_obj,
                status=Category.PENDING,
                defaults={"author": request.user},
            )
            print(f"Category created: {category_obj.name}")

        elif isinstance(category, int):
            category_obj = Category.objects.get(id=category)
            print(f"Category exists: {category_obj.name}")

        created_items = []
        for item_data in request.data:
            item_data["category"] = category_obj.id

            vehicle_specs_obj = None  

            # if category_obj.vehicle_specs.exists():

            if any(key in item_data for key in ["make", "model", "model_year"]):
                vehicle_specs_obj = handle_vehicle_specs(item_data, category_obj)

            serializer = PostItemSerializer(data=item_data, context={"request": request})
            if not serializer.is_valid():
                print(f"Validation errors: {serializer.errors}")
                return Response(
                    message="Validation error",
                    errors=serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            item = serializer.save(vehicle_specs=vehicle_specs_obj)  
            if vehicle_specs_obj:
                vehicle_specs_obj.item = item
                vehicle_specs_obj.save()
                print(f"تم الربط: {vehicle_specs_obj} -> Item {item.id}")

            created_items.append(serializer.data)

        return Response(
            message="Items created successfully",
            data=created_items,
            status=status.HTTP_201_CREATED,
        )        
        
        
    # def post(self, request):
    #         print(
    #             "Entering the post of creating a new item with category:", request.data[0]
    #         )
    #         category = request.data[0].get("category")
    #         category_group = request.data[0].get("category_group")
    #         category_type = request.data[0].get("category_type")
    #         print("Category:", category)
    #         print("Category Group:", category_group)
    #         print("Category Type:", category_type)
    #         if isinstance(category_group, str):
    #             print("Creating category group")
    #             category_group_obj, created = CategoryGroup.objects.get_or_create(
    #                 name=category_group,
    #                 group_type=category_type,
    #                 status=CategoryGroup.PENDING,  # Assuming `category_type` is passed and needs to be set in CategoryGroup
    #             )
    #             print(f"Category group created: {category_group_obj.name}")

    #         elif isinstance(category_group, int):
    #             category_group_obj = CategoryGroup.objects.get(id=category_group)
    #             print(f"Category group exists: {category_group_obj.name}")

    #         if isinstance(category, str):
    #             category_obj, created = Category.objects.get_or_create(
    #                 name=category,
    #                 category_group=category_group_obj,  # Link to the created or fetched category group
    #                 status=Category.PENDING,
    #             )
    #             print(f"Category created: {category_obj.name}")

    #         elif isinstance(category, int):
    #             category_obj = Category.objects.get(id=category)
    #             print(f"Category exists: {category_obj.name}")
                
                

    #         created_items = []
    #         for item_data in request.data:
    #             item_data["category"] = category_obj.id
                
    #             vehicle_specs_obj = None
    #             if category_obj.vehicle_specs.exists():
    #             vehicle_specs_obj = handle_vehicle_specs(item_data, category_obj)
                    
                
                    
                
                 
                
                
                
    #             serializer = PostItemSerializer(
    #                 data=item_data, context={"request": request}
    #             )
    #             if not serializer.is_valid():
    #                 print(
    #                     f"Validation errors: {serializer.errors}"
    #                 )  # This will print the detailed validation errors

    #                 return Response(
    #                     message="Validation error",
    #                     errors=serializer.errors,
    #                     status=status.HTTP_400_BAD_REQUEST,
    #                 )
    #             serializer.save()
    #             created_items.append(serializer.data)

    #         return Response(
    #             message="Items created successfully",
    #             data=created_items,
    #             status=status.HTTP_201_CREATED,
    #         )
       
                
    # def post(self, request):
    #     print("Received request data:", request.data)
    #     print("Entering the post of creating a new item with category:", request.data[0])
        
    #     category = request.data[0].get("category")
    #     category_group = request.data[0].get("category_group")
    #     category_type = request.data[0].get("category_type")
    #     print("Category:", category)
    #     print("Category Group:", category_group)
    #     print("Category Type:", category_type)

    #     if isinstance(category_group, str):
    #         print("Creating category group")
    #         category_group_obj, created = CategoryGroup.objects.get_or_create(
    #             name=category_group,
    #             group_type=category_type,
    #             status=CategoryGroup.PENDING,
    #         )
    #         print(f"Category group created: {category_group_obj.name}")

    #     elif isinstance(category_group, int):
    #         category_group_obj = CategoryGroup.objects.get(id=category_group)
    #         print(f"Category group exists: {category_group_obj.name}")

    #     if isinstance(category, str):
    #         category_obj, created = Category.objects.get_or_create(
    #             name=category,
    #             category_group=category_group_obj,
    #             status=Category.PENDING,
    #         )
    #         print(f"Category created: {category_obj.name}")

    #     elif isinstance(category, int):
    #         category_obj = Category.objects.get(id=category)
    #         print(f"Category exists: {category_obj.name}")

    #     created_items = []

    #     for item_data in request.data:
    #         item_data["category"] = category_obj.id

            
    #         vehicle_specs_obj = None

    #         make = item_data.get("make")
    #         model = item_data.get("model")
    #         model_year = item_data.get("model_year")

            
    #         if category_obj.vehicle_specs.exists() or any([make, model, model_year]):
                
                
    #             if make == "Other":
    #                 make_value = item_data.get("make_value")
    #                 if not make_value:
    #                     return Response(
    #                         {"error": "يجب إدخال قيمة make عند اختيار Other"},
    #                         status=status.HTTP_400_BAD_REQUEST,
    #                     )
    #                 make = make_value

                
    #             if model == "Other":
    #                 model_value = item_data.get("model_value")
    #                 if not model_value:
    #                     return Response(
    #                         {"error": "يجب إدخال قيمة model عند اختيار Other"},
    #                         status=status.HTTP_400_BAD_REQUEST,
    #                     )
    #                 model = model_value

                
    #             if model_year == "Other":
    #                 model_year_value = item_data.get("model_year_value")
    #                 if not model_year_value:
    #                     return Response(
    #                         {"error": "يجب إدخال قيمة model_year عند اختيار Other"},
    #                         status=status.HTTP_400_BAD_REQUEST,
    #                     )
    #                 model_year = model_year_value

                
    #             if not all([make, model, model_year]):
    #                 return Response(
    #                     {"error": "جميع الحقول (make, model, model_year) مطلوبة عند إدخال vehicle_specs"},
    #                     status=status.HTTP_400_BAD_REQUEST,
    #                 )

                
    #             vehicle_spec = category_obj.vehicle_specs.filter(
    #                 make=make,
    #                 model=model,
    #                 model_year=model_year
    #             ).first()

                
    #             if not vehicle_spec:
    #                 vehicle_spec = VehicleSpecs.objects.create(
    #                     make=make,
    #                     model=model,
    #                     model_year=model_year,
    #                     categories=category_obj,
    #                     status="pending"
    #                 )
    #                 print(f" VehicleSpecs جديدة أُنشئت وربطت بالكاتيجوري: {vehicle_spec}")

    #             vehicle_specs_obj = vehicle_spec
    #             # item_data["vehicle_specs"] = vehicle_specs_obj.id

    #         else:
    #             item_data["vehicle_specs"] = None

            
    #         serializer = PostItemSerializer(data=item_data, context={"request": request})
    #         if not serializer.is_valid():
    #             print(f"Validation errors: {serializer.errors}")
    #             return Response(
    #                 {"message": "Validation error", "errors": serializer.errors},
    #                 status=status.HTTP_400_BAD_REQUEST,
    #             )

    #         item = serializer.save(vehicle_specs=vehicle_specs_obj)


            
    #         if vehicle_specs_obj:
    #             vehicle_specs_obj.item = item  
    #             vehicle_specs_obj.save()
    #             print(f" ربط VehicleSpecs بالـ item: {item.id}")

    #         created_items.append(serializer.data)

    #     return Response(
    #         {"message": "Items created successfully", "data": created_items},
    #         status=status.HTTP_201_CREATED,
    #     )


class UserItemDetailView(APIView):
    permission_classes = [IsBusinessComplete]

    def get(self, request, pk):
        try:
            item = Item.objects.get(id=pk)
        except Item.DoesNotExist:
            return Response(
                message="Not found",
                errors={"type": ErrorTypes.NOT_FOUND, "message": "Item not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if item.owner != request.user:
            return Response(
                message="Unauthorized",
                errors={
                    "type": ErrorTypes.UNAUTHORIZED,
                    "message": "You are not authorized to edit this item",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = ItemSerializer(item, context={"request": request})
        return Response(
            message="Item detail fetched successfully",
            data=serializer.data,
            status=status.HTTP_200_OK,
        )


    def patch(self, request, pk):
            if (
                not request.user.business_profile.status
                == request.user.business_profile.APPROVED
            ):
                return Response(
                    {"error": "Your business profile is not approved"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            vehicle_specs_obj = None    
            try:
                item = Item.objects.get(id=pk)
            except Item.DoesNotExist:
                return Response(
                    message="Not found",
                    errors={"type": ErrorTypes.NOT_FOUND, "message": "Item not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if item.owner != request.user:
                return Response(
                    message="Unauthorized",
                    errors={
                        "type": ErrorTypes.UNAUTHORIZED,
                        "message": "You are not authorized to edit this item",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            old_category = CategorySerializer(item.category).data
            # print("testttt", old_category.get('category_group'))
            # print('old cat:', old_category)
            # print('pk:', pk)
            # print('request.data:',request.data)

                    
            # print('\n\n')
            print('----------------------------------------------------------------------------------------------')
            print('//////////////////////////////////////////////////////////////////////////////////////////////')
            print('old request data',request.data)

            new_category_obj = old_category
            category_group_obj = old_category.get('category_group')



            availabe_cat= request.data.get('category')
            
            if request.data.get('category'):

                new_category=request.data.get('category')
                del request.data['category']
                # change category 
                if isinstance(new_category, int):
                    new_category_obj = CategorySerializer(Category.objects.get(id=new_category)).data
                # new category
                elif isinstance(new_category, str):
                    
                    category_group = request.data.get('category_group')
                    if category_group:
                        # change in category group and new category
                        if isinstance(category_group, int):
                            category_group_obj = CategoryGroup.objects.get(id=category_group)
                            print('//////////////////////////////////////////////////////////////////////////////////////////////')
                            print(f'Category group exists: {category_group_obj.name}')
                        # new category group and new category
                        elif isinstance(category_group, str):
                            category_group_obj, created = CategoryGroup.objects.get_or_create(
                                name=category_group,
                                group_type= request.data.get('category_type'),
                                defaults={'status': CategoryGroup.PENDING}
                            )
                            print('//////////////////////////////////////////////////////////////////////////////////////////////')
                            print(f'Category group created: {category_group_obj.name}')
                        
                        new_category_obj, created = Category.objects.get_or_create(
                            name=new_category,
                            category_group=category_group_obj,
                            defaults={'status': Category.PENDING,
                                      'author': request.user
                                      }
                        )
                        print('//////////////////////////////////////////////////////////////////////////////////////////////')
                        print(f'Category created: {new_category_obj.name}')
                    
                    else:
                        new_category_obj, created = Category.objects.get_or_create(
                            name=new_category,
                            category_group=old_category.get('category_group'),
                            defaults={'status': Category.PENDING,
                                    'author': request.user
                                                                            }
                        )
                        print('//////////////////////////////////////////////////////////////////////////////////////////////')
                        print(f'Category created: {new_category_obj.name}')

                category_object=None
                if isinstance(new_category_obj, Category):
                    category_object = new_category_obj
                    new_category_obj = CategorySerializer(new_category_obj).data
                else:
                    category_object = Category.objects.get(id=new_category_obj.get("id"))
                final_cat=CategorySerializer(category_object).data



                

                
                
                
                
                request.data['category'] = final_cat.get('id')
                # vehicle_specs_obj = None
                
                if item.vehicle_specs:
                    vehicle_specs_obj = item.vehicle_specs
                    
                    vehicle_specs_obj = handle_vehicle_specs(request.data, item.category)
                    vehicle_specs_obj.save()
                elif final_cat.get("id"): 
                    category_obj = Category.objects.get(id=final_cat["id"])
                    if category_obj.category_group.group_type == "rental":
                        vehicle_specs_obj = category_obj.vehicle_specs.filter(make=request.data.get("make"),model=request.data.get("model"),model_year=request.data.get("model_year")).first()
                        if vehicle_specs_obj:
                            vehicle_specs_obj = handle_vehicle_specs(request.data, category_obj)
                            vehicle_specs_obj.save()
                            
                            
            
                        # vehicle_specs_obj = handle_vehicle_specs(request.data, category_obj) 
                    else:
                        vehicle_specs_obj = handle_vehicle_specs(request.data, category_obj)
                        # vehicle_specs_obj = None

                
                
                print('//////////////////////////////////////////////////////////////////////////////////////////////')
                print('\n\nnew category request Data:', new_category_obj)
                request.data['category'] = new_category_obj.get('id')
                print('\n\n')
                print('//////////////////////////////////////////////////////////////////////////////////////////////')
                print('new request data',request.data)
                
                
            



            # category = request.data.get('category')
            # category_group = request.data.get('category_group')
            serializer = ItemEditApproveSerializer(item, data=request.data, partial=True, context={'request': request})
            print('//////////////////////////////////////////////////////////////////////////////////////////////')
            print('serializer data:', serializer.is_valid)


            if not serializer.is_valid():
                print(serializer.errors)
                return Response(
                    message="Validation error",
                    errors=serializer.errors,
                    serializer=True,
                    status=status.HTTP_400_BAD_REQUEST,
                )
            updated_item=serializer.save()
            if vehicle_specs_obj and updated_item.category.category_group.group_type == "rental":
                updated_item.vehicle_specs = vehicle_specs_obj
                updated_item.save()
                print(f" تم ربط `VehicleSpecs` الجديد بالـ `Item`: {updated_item.id}")
                # item.vehicle_specs = vehicle_specs_obj
                # item.save()
                
            if availabe_cat:

                print("\n\nserializer data:", serializer.data)
                print("\n\nfinal category:", final_cat)
            data = (
                serializer.validated_data.copy()
            )  # Use validated_data to modify if saving directly
            if availabe_cat:
                data["category"] = final_cat
                print("\n\nfinal data:", data)

            return Response(
                message="Item updated successfully", data=data, status=status.HTTP_200_OK
            )
            
            

    def delete(self, request, pk):
        try:
            item = Item.objects.get(id=pk)
        except Item.DoesNotExist:
            return Response(
                {"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND
            )
        if item.owner != request.user:
            return Response(
                message="Unauthorized",
                errors={
                    "type": ErrorTypes.UNAUTHORIZED,
                    "message": "You are not authorized to edit this item",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        item.delete()
        return Response(message="Item deleted successfully", status=status.HTTP_200_OK)
    
class FilteredItemListView(APIView):
    permission_classes = [AllowAny]  # Permet l'accès public, optionnel

    def get(self, request):
        category = request.query_params.get('category')  # Utiliser 'category' au lieu de 'category_id'
        min_price = request.query_params.get('minPrice')  # Assurez-vous que la clé correspond à ce que vous utilisez dans l'URL
        max_price = request.query_params.get('maxPrice')

        items = Item.objects.all()

        # Filtrer par catégorie
        if category:
            items = items.filter(category__name__icontains=category)  # On suppose que `category.name` est un champ texte

        # Filtrer par prix minimum et maximum
        if min_price:
            try:
                items = items.filter(price__gte=float(min_price))
            except ValueError:
                pass  # Ignore invalid values

        if max_price:
            try:
                items = items.filter(price__lte=float(max_price))
            except ValueError:
                pass

        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)




class UserItemImageView(APIView):
    permission_classes = [IsBusinessComplete]

    def post(self, request, pk):
        # Vérification du statut business profile
        if not request.user.business_profile.status == request.user.business_profile.APPROVED:
            return Response(
                {"error": "Your business profile is not approved"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item = Item.objects.filter(id=pk)
        if not item.exists():
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
        item = item.first()

        if item.owner != request.user:
            return Response(
                {"error": "You are not authorized to add image to this item"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if item.images.count() >= 10:
            return Response({"error": "Maximum 10 images allowed"}, status=status.HTTP_400_BAD_REQUEST)

        # DEBUG : afficher ce que contient request.data et request.FILES
        print("request.data:", request.data)
        print("request.FILES:", request.FILES)

        serializer = ImageSerializer(data=request.data, context={"request": request, "item": item})

        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)  # <-- ici tu sauras exactement pourquoi ça bloque
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        item_serializer = ItemApproveSerializer(item, context={"request": request})
        return Response(item_serializer.data, status=status.HTTP_201_CREATED)


        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        item_serializer = ItemApproveSerializer(item, context={"request": request})
        return Response(item_serializer.data, status=status.HTTP_201_CREATED)


class UserItemImageDetailView(APIView):
    permission_classes = [IsBusinessComplete]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk, *args, **kwargs):
        if (
            not request.user.business_profile.status
            == request.user.business_profile.APPROVED
        ):
            return Response(
                {"error": "Your business profile is not approved"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item = Item.objects.filter(id=pk).first()
        if not item:
            return Response(
                {"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND
            )
        if item.owner != request.user:
            return Response(
                {"error": "You are not authorized to add image to this item"},
                status=status.HTTP_403_FORBIDDEN,
            )

        image_file = request.FILES.get('image')
        if not image_file:
            return Response({"error": "No image provided"}, status=400)

        image = Image.objects.create(item=item, image=image_file)
        serializer = ImageSerializer(image)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class StaffVendorListView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        type = request.query_params.get("type", CategoryGroup.PRODUCT)
        vendors = User.objects.filter(
            business_profile__status=BusinessProfile.APPROVED,
            items__status=Item.PENDING,
            items__category__category_group__group_type=type,
            items__category__status=Category.APPROVED,
        ).distinct()
        serializer = StaffVendorSerializer(
            vendors, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class StaffVendorItemListView(APIView):
    permission_classes = [IsStaff]

    def get(self, request, cr_number):
        print('this is 2')
        business_profile = BusinessProfile.objects.filter(cr_number=cr_number)
        if not business_profile.exists():
            return Response(
                {"error": "Business profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        business_profile = business_profile.first()
        type = request.query_params.get("type", CategoryGroup.PRODUCT)
        items = business_profile.user.items.filter(
            status=Item.PENDING, category__category_group__group_type=type
        )
        serializer = ItemApproveSerializer(
            items, many=True, context={"request": request}
        )
        return Response(
            message="Pending items fetched successfully",
            data=serializer.data,
            status=status.HTTP_200_OK,
        )


class ItemDetailApproveView(APIView):
    permission_classes = [IsStaff]

    def post(self, request, pk):
        item = Item.objects.filter(id=pk)
        if not item.exists():
            return Response(
                {"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND
            )
        item = item.first()
        if item.status == Item.APPROVED:
            return Response(
                {"error": "Item already approved"}, status=status.HTTP_400_BAD_REQUEST
            )
        item.status = Item.APPROVED
        item.staff_note = request.data.get("staff_note", "")
        item.save()
        return Response(
            {"message": "Item approved successfully"}, status=status.HTTP_200_OK
        )


class ItemDetailRejectView(APIView):
    permission_classes = [IsStaff]

    def post(self, request, pk):
        item = Item.objects.filter(id=pk)
        if not item.exists():
            return Response(
                {"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND
            )
        item = item.first()
        if item.status == Item.REJECTED:
            return Response(
                {"error": "Item already rejected"}, status=status.HTTP_400_BAD_REQUEST
            )
        item.status = Item.REJECTED
        item.staff_note = request.data.get("staff_note", "")
        item.save()
        return Response(
            {"message": "Item rejected successfully"}, status=status.HTTP_200_OK
        )

class VehicleSpecsListPendingView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        
        pending_vehicle_specs = VehicleSpecs.objects.filter(status="pending")
        serializer = VehicleSpecsSerializer(
            pending_vehicle_specs, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class VehicleSpecsDetailApproveView(APIView):
    permission_classes = [IsStaff]

    def post(self, request, pk):
        try:
            vehicle_spec = VehicleSpecs.objects.get(id=pk, status="pending")
        except VehicleSpecs.DoesNotExist:
            return Response(
                {"error": "VehicleSpecs not found or already processed"},
                status=status.HTTP_404_NOT_FOUND
            )

        
        vehicle_spec.status = "approved"
        vehicle_spec.save()

        return Response(
            {"message": "VehicleSpecs approved successfully"},
            status=status.HTTP_200_OK
        )


class VehicleSpecsDetailRejectView(APIView):
    permission_classes = [IsStaff]

    def post(self, request, pk):
        try:
            vehicle_spec = VehicleSpecs.objects.get(id=pk, status="pending")
        except VehicleSpecs.DoesNotExist:
            return Response(
                {"error": "VehicleSpecs not found or already processed"},
                status=status.HTTP_404_NOT_FOUND
            )

        
        vehicle_spec.status = "rejected"
        vehicle_spec.save()

        return Response(
            {"message": "VehicleSpecs rejected successfully"},
            status=status.HTTP_200_OK
        )

class CategoryListPendingView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        category = Category.objects.filter(status="pending")
        serializer = CategorySerializer(
            category, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


    
class CategoryDetailApproveView(APIView):
    permission_classes = [IsStaff]

    def post(self, request, pk):
        category = Category.objects.filter(id=pk)
        if not category.exists():
            return Response(
                {"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND
            )
        category = category.first()
        print("Categoryy:", category.name)
        if category.status == Category.APPROVED:
            return Response(
                {"error": "Category already approved"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CategorySerializer(
            category, data=request.data, partial=True, context={"request": request}
        )
        if not serializer.is_valid():
            print(
                f"Validation errors: {serializer.errors}"
            )  # This will print the detailed validation errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        return Response(
            {"message": "Category approved successfully"}, status=status.HTTP_200_OK
        )


class CategoryDetailRejectView(APIView):
    permission_classes = [IsStaff]

    def post(self, request, pk):
        category = Category.objects.filter(id=pk)
        if not category.exists():
            return Response(
                {"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND
            )
        category = category.first()
        if category.status == Category.REJECTED:
            return Response(
                {"error": "Category already rejected"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        category.status = Category.REJECTED
        category.save()

        category_group = category.category_group
        if category_group.status == CategoryGroup.PENDING:
            category_group.status = CategoryGroup.REJECTED
            category_group.save()

        return Response(
            {"message": "Category rejected successfully"}, status=status.HTTP_200_OK
        ) # subitem = get_object_or_404(SubItem, id=subitem_id)


class CertificateListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        certificates = CertificateType.objects.all()
        serializer = CertificateTypeSerializer(
            certificates, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

class UploadFilesSubItemView(APIView):
    permission_classes = [IsBusinessComplete]
    parser_classes = [MultiPartParser, FormParser]
 
    def post(self, request, format=None):
        
        
        try:
            print("📦 Raw Request Data:", request.data)
            print("📁 FILES Received:", request.FILES)
            subitems_data = json.loads(request.data.get('subitems', '[]'))
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON format in 'subitems'"}, status=status.HTTP_400_BAD_REQUEST)

        if not subitems_data:
            return Response({"error": "subitems list is required"}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_files = []

        for subitem_entry in subitems_data:
            subitem_id = subitem_entry.get('subitem_id')
            if str(subitem_id).startswith('tmp_'):
               subitem = SubItem.objects.filter(value=subitem_id).first()
               if not subitem:
                   return Response({"error": f"SubItem with value '{subitem_id}' not found"}, status=status.HTTP_404_NOT_FOUND)
            else:
                subitem = get_object_or_404(SubItem, id=subitem_id)
                

            files = [f for key, f in request.FILES.items() if key.startswith(f'files_{subitem_id}_')]

            # files = request.FILES.getlist(f'files_{subitem_id}')
            
            # expiry_dates = request.data.getlist(f'expiry_date_files_{subitem_id}')
            expiry_dates = [v for k, v in request.data.items() if k.startswith(f'expiry_date_files_{subitem_id}_')]
            certificate_ids = [v for k, v in request.data.items() if k.startswith(f'certificate_type_{subitem_id}_')]

            # certificate_ids = request.data.getlist(f'certificate_type_{subitem_id}')  

            if not files:
                return Response({"error": f"No files provided for subitem {subitem_id}"}, status=status.HTTP_400_BAD_REQUEST)

            ### subitem = get_object_or_404(SubItem, id=subitem_id)
            
            for key, f in request.FILES.items():
                if not key.startswith(f'files_{subitem_id}_'):
                    continue

                # مثال على key: files_tmp_1742159928506_AramcoCertificate أو files_tmp_1742159928506_1
                suffix = key.replace(f'files_{subitem_id}_', '')

                expiry_key = f'expiry_date_files_{subitem_id}_{suffix}'
                certificate_key = f'certificate_type_{subitem_id}_{suffix}'

                expiry_date = request.data.get(expiry_key)
                certificate_id = request.data.get(certificate_key)
                print("🧾 Looking for:", certificate_key)
                print("✅ Found certificate_id:", certificate_id)


                serializer = UploadFilesSubItemSerializer(data={
                    'file': f,
                    'expiry_date': expiry_date,
                    'certificate_type_id': certificate_id
                })
                if serializer.is_valid():
                    serializer.save(subitem=subitem)
                    uploaded_files.append(serializer.data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
            for key, image_file in request.FILES.items():
                if not key.startswith(f'image_{subitem_id}_'):
                    continue

                upload_instance =UploadImagesSubItems.objects.create(
                    subitem=subitem,
                    image=image_file,
                    is_thumbnail=False
                ) 
                # if subitem.images.count() == 1:
                Image.objects.create(
                    item=subitem.item,
                    image=upload_instance.image,
                    is_thumbnail=True
                )


            # for idx, f in enumerate(files):
            #     expiry_date = expiry_dates[idx] if idx < len(expiry_dates) else None
            #     certificate_id = certificate_ids[idx] if idx < len(certificate_ids) else None

            #     serializer = UploadFilesSubItemSerializer(data={
            #         'file': f,
            #         'expiry_date': expiry_date,
            #         'certificate_type_id': certificate_id
            #     })
            #     if serializer.is_valid():
            #         serializer.save(subitem=subitem)
            #         uploaded_files.append(serializer.data)
            #     else:
            #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "Files uploaded successfully",
            "uploaded_files": uploaded_files
        }, status=status.HTTP_201_CREATED)
        
# class UploadFilesSubItemView(APIView):
#     parser_classes = [MultiPartParser, FormParser]
    
    

#     def post(self, request, format=None):
#         print("🔥 Request Data:", request.data)
#         print("🔥 Request FILES:", request.FILES)
#         try:
            
#             subitems_data = json.loads(request.data.get('subitems', '[]'))
#         except json.JSONDecodeError:
#             return Response({"error": "Invalid JSON format in 'subitems'"}, status=status.HTTP_400_BAD_REQUEST)

#         if not subitems_data:
#             return Response({"error": "subitems list is required"}, status=status.HTTP_400_BAD_REQUEST)

#         uploaded_files = []

#         for subitem_entry in subitems_data:
#             subitem_id = subitem_entry.get('subitem_id')
#             if not subitem_id:
#                 return Response({"error": "subitem_id is required"}, status=status.HTTP_400_BAD_REQUEST)

#             subitem = get_object_or_404(SubItem, id=subitem_id)

            
#             file_keys = [key for key in request.FILES if key.startswith(f'files_{subitem_id}_')]
#             if not file_keys:
#                 return Response({"error": f"No files provided for subitem {subitem_id}"}, status=status.HTTP_400_BAD_REQUEST)

#             for file_key in file_keys:
#                 file = request.FILES[file_key]
#                 expiry_date = request.data.get(f'expiry_date_{file_key}', None)  

#                 serializer = UploadFilesSubItemSerializer(data={'file': file, 'expiry_date': expiry_date})
#                 if serializer.is_valid():
#                     serializer.save(subitem=subitem)
#                     uploaded_files.append(serializer.data)
#                 else:
#                     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         return Response({
#             "message": "Files uploaded successfully",
#             "uploaded_files": uploaded_files
#         }, status=status.HTTP_201_CREATED)


        
    # def post(self, request, format=None):
        
    #     subitem_id = request.data.get('subitem_id')
    #     if not subitem_id:
    #         return Response({"error": "subitem_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        
    #     subitem = get_object_or_404(SubItem, id=subitem_id)
        
        
    #     files = request.FILES.getlist('files')
    #     if not files:
    #         return Response({"error": "No files provided"}, status=status.HTTP_400_BAD_REQUEST)
        
    #     uploaded_files = []
        
    #     expiry_date = request.data.get('expiry_date')
        
    #     for f in files:
    #         serializer = UploadFilesSubItemSerializer(data={'file': f, 'expiry_date': expiry_date})
    #         if serializer.is_valid():
    #             serializer.save(subitem=subitem)
    #             uploaded_files.append(serializer.data)
    #         else:
    #             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    #     return Response({
    #         "message": "Files uploaded successfully",
    #         "uploaded_files": uploaded_files
    #     }, status=status.HTTP_201_CREATED)





#         category = Category.objects.filter(id=pk)
#         if not category.exists():
#             return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

#         category = category.first()

#         # Fetch the associated categories for the given category
#         category_associates = category.category_association.all()  # Assuming it's a related manager or reverse relationship

#         if not category_associates:
#             return Response({'message': 'No associated categories found'}, status=status.HTTP_200_OK)

#         # Serialize the associated categories
#         serializer = CategorySerializer(category_associates, many=True, context={'request': request})

#         # Return the response with serialized data
#         return Response({'associated_categories': serializer.data}, status=status.HTTP_200_OK)

# class UserRentalItemListView(ListAPIView):
#     permission_classes = [IsBusinessComplete]
#     pagination_class = PageNumberPagination
#     serializer_class = RentalItemSerializer

#     def get_queryset(self):
#         query = RentalItem.objects.filter(item__owner=self.request.user)
#         return query

#     def get(self, request):
#         queryset = self.get_queryset()
#         filterSerializer = FilterUserItemSerializer(data=request.GET)
#         if not filterSerializer.is_valid():
#             return Response(message="Validation error", errors=filterSerializer.errors, serializer=True, status=status.HTTP_400_BAD_REQUEST)

#         if request.GET.get('category_group'):
#             queryset = queryset.filter(category__category_group__group_type=request.GET.get('category_group'))
#         if request.GET.get('query'):
#             query = request.GET.get('query').lower().strip()
#             queryset = queryset.filter(Q(name__icontains=query) | Q(owner__name__icontains=query) | Q(category__name__icontains=query))

#         page = self.paginate_queryset(queryset)
#         if page is not None:
#             serializer = self.serializer_class(page, many=True , context=self.get_serializer_context())
#             return self.get_paginated_response(serializer.data)
#         serializer = self.serializer_class(queryset, many=True, context=self.get_serializer_context())
#         return Response(message="Items fetched successfully", data=serializer.data, status=status.HTTP_200_OK)


# class ItemListView(APIView):
#     permission_classes = [AllowAny]

#     def get(self, request):
#         items = Item.objects.filter(status=Item.APPROVED)

#         # apply search filters
#         if 'q' in request.query_params:
#             items = items.filter(Q(name__icontains=request.query_params['q']) |
#                                  Q(owner__name__icontains=request.query_params['q']) |
#                                  Q(category__name__icontains=request.query_params['q']) |
#                                  Q(category__category_group__name__icontains=request.query_params['q']))

#         # apply category filters
#         if 'category' in request.query_params:
#             items = items.filter(category__category_group__id__in=request.query_params['category'].split(','))

#         # apply type filters
#         if 'type' in request.query_params:
#             items = items.filter(category__category_group__group_type__in=request.query_params['type'].split(','))

#         # apply field filters
#         field_types = FieldType.objects.all()
#         for field in field_types:
#             if field.name in include_search_fields and field.extra_fields.count() > 0 and field.name in request.query_params:
#                 items = items.filter(extrafield__type__name=field.name, extrafield__value__in=request.query_params[field.name].split(','))

#         # apply sort filters
#         if 'sort' in request.query_params:
#             if request.query_params['sort'] == 'price_asc':
#                 items = items.order_by('price')
#             elif request.query_params['sort'] == 'price_desc':
#                 items = items.order_by('-price')

#         serializer = ItemSerializer(items, many=True, context={'request': request})
#         return Response(message="Items fetched successfully", data=serializer.data, status=status.HTTP_200_OK)
