from django.db.models import Q
from django.utils import timezone
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.views import APIView
from driver.models import DriverOrderTracking

from .models import Order, OrderItem,OrderItemReport,OrderTracking
from .serializers import (
    OrderSerializer,
    OrderFilterSerializer,
    FilterOrderSerializer,
    OrderBillSerializer,
    OrderCreateSerializer,
    DisposalCertificateSerializer,
    OrderItemReportSerializer,
    OrderContractsSerializer,
)
from .moyasar import fetch_payment
from scraapy.permissions import IsBusiness, IsBusinessComplete, IsDriver
from inventory.serializers import ItemSerializer
from inventory.models import Item,CategoryGroup
from .utils import get_shipping_options

from external.pythonlibrary.api_responses.die import Response
from external.pythonlibrary.api_responses.error_types import ErrorTypes

import datetime
import math

class BillList(ListAPIView):
    permission_classes = [IsBusiness]
    pagination_class = PageNumberPagination
    serializer_class = OrderBillSerializer

    def get_queryset(self):
        user = self.request.user
        query = Q(buyer=user) & (Q(status="paid") | Q(status="completed"))
        orders = Order.objects.filter(query)
        return orders

    def get(self, request):
        # user = self.request.user

        # try:
        #     company = Company.objects.get(staff_company__user = user , staff_company__role = Staff.ADMIN)
        # except Company.DoesNotExist:
        #     return Response(message="No company found", errors={'type': ErrorTypes.NOT_FOUND, 'message': 'No company found for this id'}, status=status.HTTP_404_NOT_FOUND)

        # if user.company != company and not company.company_properties.filter(owners=user).exists():
        #     return Response(message="No permissions", errors={'type': ErrorTypes.PERMISSION, 'message': 'User does not have permissions to view bill'}, status=status.HTTP_401_UNAUTHORIZED)

        queryset = self.get_queryset()

        # filterSerializer = FilterBillSerializer(data=request.GET)
        # if not filterSerializer.is_valid():
        #     return Response(message="Validation error", errors=filterSerializer.errors, serializer=True, status=status.HTTP_400_BAD_REQUEST)

        # if request.GET.get('type'):
        #     queryset = queryset.filter(type=request.GET.get('type'))
        # if request.GET.get('tenant'):
        #     tenant = request.GET.get('tenant').lower().strip()
        #     queryset = queryset.filter(Q(tenant__user__name__icontains=tenant) | Q(tenant__organization__name__icontains=tenant))
        # if request.GET.get('status'):
        #     queryset = queryset.filter(status=request.GET.get('status'))
        # if request.GET.get('query'):
        #     query = request.GET.get('query').lower().strip()
        #     queryset = queryset.filter(Q(title__icontains=query))

        # # Time-based filters
        # start_date = request.GET.get('start_date')
        # end_date = request.GET.get('end_date')

        # if start_date:
        #     try:
        #         # Convert start_date to datetime
        #         start_datetime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        #         queryset = queryset.filter(issue_date__gte=start_datetime)
        #     except ValueError:
        #         return Response({
        #             "message": "Invalid start_date format. Use YYYY-MM-DD."
        #         }, status=status.HTTP_400_BAD_REQUEST)

        # if end_date:
        #     try:
        #         # Convert end_date to datetime
        #         end_datetime = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        #         queryset = queryset.filter(due_date__lte=end_datetime)
        #     except ValueError:
        #         return Response({
        #             "message": "Invalid end_date format. Use YYYY-MM-DD."
        #         }, status=status.HTTP_400_BAD_REQUEST)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(queryset, many=True)
        return Response(
            message="Bills fetched successfully",
            data=serializer.data,
            status=status.HTTP_200_OK,
        )


# changed to order
class BillDetail(APIView):
    permission_classes = [IsBusiness]

    def get(self, request, pk):
        user = request.user

        try:
            order = Order.objects.get(id=pk, buyer=user, status="paid")
        except Order.DoesNotExist:
            return Response(
                message="No Bill found",
                errors={
                    "type": ErrorTypes.NOT_FOUND,
                    "message": "No Bill found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = OrderBillSerializer(order)
        return Response(
            message="Bill fetched successfully",
            data=serializer.data,
            status=status.HTTP_200_OK,
        )
    
class CheckOutSuggestion(APIView):
    permission_classes = [IsAuthenticated]
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        R = 6371  # نصف قطر الأرض بالكيلومتر
        return R * c
    
    def get(self, request):
            buyer_lat = request.GET.get("latitude")
            buyer_lon = request.GET.get("longitude")
            try:
                buyer_lat = float(buyer_lat) if buyer_lat else None
                buyer_lon = float(buyer_lon) if buyer_lon else None
            except ValueError:
                buyer_lat, buyer_lon = None, None

            if buyer_lat is None or buyer_lon is None:
                try:
                    buyer_lat = float(request.user.address.latitude)
                    buyer_lon = float(request.user.address.longitude)
                except Exception:
                    buyer_lat, buyer_lon = None, None

            item_ids = request.GET.getlist("item_ids", [])
            province = request.GET.get("province")
            additional_services = {}
            contracts = {}
            total_shipping_cost = None
            has_null_shipping = False

            for id in item_ids:
                try:
                    item = Item.objects.get(pk=id)
                except Item.DoesNotExist:
                    continue

                if hasattr(item.category, 'shipping_rate') and item.category.shipping_rate:
                    rate_per_km = item.category.shipping_rate.rate_per_km
                else:
                    rate_per_km = None
                    has_null_shipping = True

                additional_services.update({id: {}})
                associated_categories = item.category.associated_categories.filter(
                    category_group__group_type=CategoryGroup.SERVICE
                ).all()

                for ac in associated_categories:
                    items = Item.objects.filter(category=ac, status=Item.APPROVED)
                    if province:
                        items = items.filter(province=province)
                    if buyer_lat is not None and buyer_lon is not None:
                        bounding_box = 70
                        min_lat = buyer_lat - (bounding_box / 111.32)
                        max_lat = buyer_lat + (bounding_box / 111.32)
                        min_lon = buyer_lon - (bounding_box / (111.32 * math.cos(math.radians(buyer_lat))))
                        max_lon = buyer_lon + (bounding_box / (111.32 * math.cos(math.radians(buyer_lat))))
                        items = items.filter(
                            latitude__gte=min_lat,
                            latitude__lte=max_lat,
                            longitude__gte=min_lon,
                            longitude__lte=max_lon,
                        )
                    serializer = ItemSerializer(items[:6], many=True, context={"request": request})
                    additional_services[id].update({ac.name: serializer.data})

                try:
                    seller_lat = float(item.latitude)
                    seller_lon = float(item.longitude)
                except (ValueError, TypeError):
                    return Response(
                        {"message": f"Seller coordinates not provided for item id {id}."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # distance = self.haversine_distance(buyer_lat, buyer_lon, seller_lat, seller_lon)
                if buyer_lat is not None and buyer_lon is not None and seller_lat is not None and seller_lon is not None:
                    distance = self.haversine_distance(buyer_lat, buyer_lon, seller_lat, seller_lon)
                else:
                    distance = 0
                    has_null_shipping = True


                # if rate_per_km is None or rate_per_km < 0:
                if rate_per_km is None or rate_per_km < 0 or distance == 0:
                    shipping_cost = None
                else:
                    shipping_cost = distance * float(rate_per_km)
                    total_shipping_cost = shipping_cost if total_shipping_cost is None else total_shipping_cost + shipping_cost

                additional_services[id].update({
                    "shipping_info": {
                        "distance_km": round(distance, 3),
                        "shipping_cost": round(shipping_cost, 3) if shipping_cost is not None else None
                    }
                })

                
                contracts.update({id: {}})
                if item.category.require_contract:
                    contract = item.category.contract_text
                    seller_info = f"**إسم البائع:** {item.owner.name}\n**بريد البائع:** {item.owner.email}"
                    buyer_info = f"**إسم المشتري:** {self.request.user.name}\n**بريد المشتري:** {self.request.user.email}"
                    selling_date = f"**تاريخ الشراء:** {datetime.datetime.now().strftime('%Y/%m/%d')}\n"
                    contract_with_info = f"{seller_info}\n\n{buyer_info}\n\n{contract}\n{selling_date}"
                    contracts[id].update({"contract_text": contract_with_info})

            if has_null_shipping:
                total_shipping_cost = None

            shipping_options = get_shipping_options(total_shipping_cost)

            data = {
                "additional_services": additional_services,
                "shipping_options": shipping_options,
                "contracts": contracts,
            }

            return Response(
                {"message": "Checkout suggestions fetched successfully"},
                data=data,
                status=status.HTTP_200_OK,
            )    
              
            
            
    # def get(self, request):
    #     #
    #     buyer_lat = request.GET.get("latitude")
    #     buyer_lon = request.GET.get("longitude")
    #     try:
    #         buyer_lat = float(buyer_lat) if buyer_lat else None
    #         buyer_lon = float(buyer_lon) if buyer_lon else None
    #     except ValueError:
    #         buyer_lat, buyer_lon = None, None
    #         # return Response({"message": "Invalid buyer coordinates."}, status=status.HTTP_400_BAD_REQUEST)
    #     #
    #     if buyer_lat is None or buyer_lon is None:
    #         try:
    #             buyer_lat = float(request.user.address.latitude)
    #             buyer_lon = float(request.user.address.longitude)
    #         except Exception:
    #             buyer_lat, buyer_lon = None, None
    #             # return Response(
    #             #     {"message": "Buyer coordinates not provided and no address available."},
    #             #     status=status.HTTP_400_BAD_REQUEST
    #             # )
    #     item_ids = request.GET.getlist("item_ids", [])
    #     province = request.GET.get("province")
    #     additional_services = {}
    #     total_shipping_cost = None
    #     has_null_shipping = False
    #     # rate_per_km = 5  # 5 ريال لكل كيلومتر
    #     for id in item_ids:
    #         try:
    #             item = Item.objects.get(pk=id)
    #         except Item.DoesNotExist:
    #             continue
            
    #         if hasattr(item.category, 'shipping_rate') and item.category.shipping_rate:
    #             rate_per_km = item.category.shipping_rate.rate_per_km
    #         else:
    #             rate_per_km = None
    #             has_null_shipping = True


    #         additional_services.update({id: {}})
    #         associated_categories = item.category.associated_categories.filter(category_group__group_type=CategoryGroup.SERVICE).all()
    #         for ac in associated_categories:
    #             items = Item.objects.filter(category=ac, status=Item.APPROVED)
    #             if province:
    #                 items = items.filter(province=province)
    #             if buyer_lat is not None and buyer_lon is not None:
    #                 bounding_box = 70  # قيمة افتراضية بالكيلومتر
    #                 min_lat = buyer_lat - (bounding_box / 111.32)
    #                 max_lat = buyer_lat + (bounding_box / 111.32)
    #                 min_lon = buyer_lon - (bounding_box / (111.32 * math.cos(math.radians(buyer_lat))))
    #                 max_lon = buyer_lon + (bounding_box / (111.32 * math.cos(math.radians(buyer_lat))))
    #                 items = items.filter(
    #                     latitude__gte=min_lat,
    #                     latitude__lte=max_lat,
    #                     longitude__gte=min_lon,
    #                     longitude__lte=max_lon,
    #                 )
    #             serializer = ItemSerializer(items[:6], many=True, context={"request": request})
    #             additional_services[id].update({ac.name: serializer.data})
    #         try:
    #             seller_lat = float(item.latitude)
    #             seller_lon = float(item.longitude)
    #         except (ValueError, TypeError):
    #             return Response(
    #                 {"message": f"Seller coordinates not provided for item id {id}."},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )
    #         distance = self.haversine_distance(buyer_lat, buyer_lon, seller_lat, seller_lon)
    #         if rate_per_km is None or rate_per_km < 0:
    #                 shipping_cost = None
    #         else:
    #             shipping_cost = distance * float(rate_per_km)
    #             total_shipping_cost = shipping_cost if total_shipping_cost is None else total_shipping_cost + shipping_cost
                
                 
                

    #         additional_services[id].update({
    #             "shipping_info": {
    #                 "distance_km": round(distance, 3),
    #                 "shipping_cost": round(shipping_cost, 3) if shipping_cost is not None else None
    #             }
    #         })
       
       
            
    #     if has_null_shipping:
    #         total_shipping_cost = None 
            
            
    #     shipping_options = get_shipping_options(total_shipping_cost)
    #     data = {
    #         "additional_services": additional_services,
    #         "shipping_options": shipping_options,
    #     }
    #     return Response(
    #         {"message": "Checkout suggestions fetched successfully"},data=data,
    #         status=status.HTTP_200_OK,
    #     )

class OrderListView(ListAPIView):
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination
    serializer_class = OrderFilterSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            user = self.request.user
            if self.request.GET.get("type") == "bought":
                return Order.objects.filter(buyer=user).distinct()
            elif self.request.GET.get("type") == "sold":
                return Order.objects.filter(order_items__owner=user).distinct()
            else:
                return None
        return Order.objects.filter(
            buyer_email=self.request.GET.get("email"), id=self.request.GET.get("id")
        )

    def get(self, request):
        if (
            not request.GET.get("type")
            and not request.GET.get("email")
            and not request.GET.get("id")
        ):
            return Response(
                message="Type, email or id is required",
                status=status.HTTP_400_BAD_REQUEST,
            )
        queryset = self.get_queryset()

        filterSerializer = FilterOrderSerializer(data=request.GET)
        if not filterSerializer.is_valid():
            return Response(
                message="Validation error",
                errors=filterSerializer.errors,
                serializer=True,
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.GET.get("is_delivery"):
            if request.GET.get("is_delivery").lower().strip() == "true":
                queryset = queryset.filter(is_delivery=(True))
            else:
                queryset = queryset.filter(is_delivery=(False))

        if request.GET.get("group_type"):
            queryset = queryset.filter(
                Q(
                    order_items__category__category_group__group_type=request.GET.get(
                        "group_type"
                    )
                )
            )
        if request.GET.get("category_group"):
            queryset = queryset.filter(
                Q(
                    order_items__category__category_group__name=request.GET.get(
                        "category_group"
                    )
                )
                | Q(
                    order_items__category__category_group__name_ar=request.GET.get(
                        "category_group"
                    )
                )
            )
        if request.GET.get("category"):
            queryset = queryset.filter(
                Q(order_items__category__name=request.GET.get("category"))
                | Q(order_items__category__name_ar=request.GET.get("category"))
            )

        if request.GET.get("status"):
            queryset = queryset.filter(status=request.GET.get("status"))
        if request.GET.get("query"):
            query = request.GET.get("query").lower().strip()
            queryset = queryset.filter(Q(id__icontains=query))

        if request.GET.get("sort") == "latest":
            queryset = queryset.order_by("-created_at")
        if request.GET.get("sort") == "oldest":
            queryset = queryset.order_by("created_at")

        # Time-based filters
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        if start_date:
            try:
                # Convert start_date to datetime
                start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                queryset = queryset.filter(created_at__gte=start_datetime)
            except ValueError:
                return Response(
                    {"message": "Invalid start_date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if end_date:
            try:
                # Convert end_date to datetime
                end_datetime = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                queryset = queryset.filter(created_at__lte=end_datetime)
            except ValueError:
                return Response(
                    {"message": "Invalid end_date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(
                page, many=True, context={"request": request,"group_type":request.GET.get("group_type")}
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(
          queryset, many=True,
          context={"request": request, "group_type": request.GET.get("group_type")}
        )

        print('the data is: ',serializer.data)
        return Response(
            message="Order list fetched successfully",
            data=serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        for item in request.data["items"]:
            try:
                item = Item.objects.get(pk=item["item"], status=Item.APPROVED)
                if item.owner== self.request.user:
                    return Response(
                    message='You are buying from your self',
                    status=status.HTTP_409_CONFLICT
                )
                if item.category.category_group.group_type == CategoryGroup.SERVICE and request.data['shipping_option'] == 2:
                    return Response(
                    message='You cannot Pick up a service',
                    status=410
                )
            except Item.DoesNotExist:
                return Response(
                    message="Item not found",
                    errors={
                        "type": ErrorTypes.NOT_FOUND,
                        "message": "No item found for this id",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
        print('the whole data for order is:',request.data)
        serializer = OrderCreateSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(
                message="Validation error",
                errors=serializer.errors,
                serializer=True,
                status=status.HTTP_400_BAD_REQUEST,
            )
        order_serializer, payment_url = serializer.save()
        serializer = OrderSerializer(order_serializer)
        return Response(
            message="Order created successfully",
            data={"payment_url": payment_url, "data": serializer.data},
            status=status.HTTP_200_OK,
        )









class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def createDriverTracking(self, order_item, driver_profile):
        print('creating order tracking')
        driver_tracking, created = DriverOrderTracking.objects.get_or_create(
            order_item=order_item,
            defaults={
                "driver": driver_profile,
                "tracking_system_address": order_item.tracking_system_addresses,
                "status": DriverOrderTracking.STARTED_JOURNEY,
            }
        )
        if not created:
            driver_tracking.driver = driver_profile
            driver_tracking.status = DriverOrderTracking.STARTED_JOURNEY
            driver_tracking.start_time = timezone.now()
            driver_tracking.save()
        return driver_tracking
    



    def get_queryset(self, order_id):
        user = self.request.user
        if user.is_authenticated:
            is_driver = hasattr(user, "driver_profile")
            query = (
                Q(buyer=user)
                | Q(order_items__owner=user)
            )
            if is_driver:
                query |= Q(order_items__driver_tracking__isnull=True) | Q(
                    order_items__driver_tracking__driver=user.driver_profile
                )
            return Order.objects.filter(query, id=order_id).first()
        return Order.objects.filter(buyer_email=self.request.GET.get("email"), id=order_id).first()
    
    def post(self, request, pk):
        require_file = False
        try:
            order = self.get_queryset(pk)
        except Order.DoesNotExist:
            return Response(message="Order not found", status=404)

        order_item_id = request.data.get("order_item_id")
        print('the order item id is:',order_item_id)
        print('the order id:',pk)
        print('the order is:',order)
        try:
            order_item = order.order_items.get(pk=order_item_id)
        except OrderItem.DoesNotExist:
            return Response(message="Order item not found", status=404)

        tracking = order_item.tracking

        # ر (هنا التغيير فقط 👇)
        user_relation = None
        if order_item.owner == request.user:
            user_relation = "seller"
        elif order.buyer == request.user:
            user_relation = "buyer"
        if hasattr(order_item, "driver_tracking") and order_item.driver_tracking:
                    if order_item.driver_tracking.driver == request.user.driver_profile:
                        user_relation = "driver"
        elif not hasattr(order_item, "driver_tracking") and hasattr(request.user, "driver_profile"):
            user_relation = "driver"

        # تحقق من صلاحية المستخدم الحالي لتغيير الحالة
        allowed_actor = dict(tracking.steps).get(tracking.status)
        if allowed_actor != user_relation:

            return Response(
                {"message": "You are not allowed to change status"},
                status=403,
            )

        # التقدم خطوة للأمام
        status, _ = zip(*tracking.steps)
        status = list(status)
        print('the status is:',status)
        index = status.index(tracking.status)
        if index == len(status) - 1:
            return Response(
                message="Cannot change status",
                status=status.HTTP_400_BAD_REQUEST,
            )
        next_status = status[index + 1]
        tracking.status = next_status




        # هنا بس نضيف دعم بسيط لتحديث حالة السائق (لو كان Driver) 👇
        if user_relation == "driver":
            driver_profile = request.user.driver_profile
            driver_tracking = DriverOrderTracking.objects.filter(
                tracking_system_address=order_item.tracking_system_addresses,
                driver=driver_profile
            ).first()
            # إذا مافيه سجل، ننشئ واحد جديد
            if not driver_tracking:
                driver_tracking = self.createDriverTracking(order_item, driver_profile)
            # نحدث الحالة
            driver_tracking.status = next_status
            if next_status == DriverOrderTracking.DROP_OFF:
                driver_tracking.end_time = timezone.now()
            driver_tracking.save()




        if order_item.category.category_group.group_type == CategoryGroup.SERVICE and next_status == OrderTracking.INSPECTING:
            require_file = True

        tracking.save()
        return Response(
            data={"require_file": require_file},
            message="Order item status changed successfully",
            status=200,
        )


    # def post(self, request, pk):
    #     require_file=False
    #     try:
    #         order = self.get_queryset(pk)
    #     except Order.DoesNotExist:
    #         return Response(
    #             message="Order not found",
    #             status=404,
    #         )
    #     order_item_id = request.data.get("order_item_id")
    #     try:
    #         order_item = order.order_items.get(pk=order_item_id)
    #     except OrderItem.DoesNotExist:
    #         return Response(
    #             message="Order item not found",
    #             status=404,
    #         )
    #     user_relation = "seller" if order_item.owner == request.user else "buyer"
    #     tracking = order_item.tracking
    #     # print('dict', dict(tracking.steps).get(tracking.status))
    #     # print('status', tracking.status)
    #     # print (order_item.owner, request.user)
    #     # print('here')
    #     if dict(tracking.steps).get(tracking.status) is not user_relation:

    #         return Response(
    #             { "message":"You are not allowed to change status"},
    #             status=401,
    #         )
    #     # increment status
    #     status, _ = zip(*tracking.steps)
    #     status = list(status)
    #     index = status.index(tracking.status)
    #     if index == len(status) - 1:
    #         return Response(
    #             message="Cannot change status",
    #             status=status.HTTP_400_BAD_REQUEST,
    #         )
    #     next_status = status[index + 1]
    #     tracking.status = next_status
    #     print('/n next status:',next_status,order_item.category.category_group.group_type)
    #     if order_item.category.category_group.group_type == CategoryGroup.SERVICE and next_status == OrderTracking.INSPECTING:
    #         require_file=True
        
    #     tracking.save()
    #     return Response(
    #         data={"require_file":require_file},
    #         message="Order item status changed successfully",
    #         status=200,
    #     )

class AssignDriverOrderItemView(APIView):
    permission_classes = [IsDriver]

    def post(self, request, order_item_id):
        try:
            order_item = OrderItem.objects.get(pk=order_item_id)
        except OrderItem.DoesNotExist:
            return Response({"message": "Order item not found"}, status=404)
            
        # تأكد من أن المستخدم هو سائق
        if not hasattr(request.user, 'driver_profile'):
            return Response({"message": "Only drivers can assign orders"}, status=401)
            
        driver_profile = request.user.driver_profile

        # قم بإنشاء أو تحديث سجل DriverOrderTracking متصل بالطلب
        driver_tracking, created = DriverOrderTracking.objects.get_or_create(
            order_item=order_item,
            defaults={
                "driver": driver_profile,
                "tracking_system_address": order_item.tracking_system_addresses,
                "status": DriverOrderTracking.STARTED_JOURNEY,
            }
        )
        if not created:
            # إن كان موجوداً مسبقاً، قم بتحديثه إذا لزم الأمر
            driver_tracking.driver = driver_profile
            driver_tracking.status = DriverOrderTracking.STARTED_JOURNEY
            driver_tracking.start_time = timezone.now()
            driver_tracking.save()

        return Response({"message": "Driver assigned to order item successfully"}, status=200)


class PaymentCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payment_id = request.data.get("id")
        payment_status = request.data.get("status")
        payment_message = request.data.get("message")
        if not payment_id:
            return Response(
                message="Payment ID is required",
                errors={
                    "type": ErrorTypes.INVALID,
                    "message": "Payment ID is required",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if payment_status and payment_status != "paid":
            return Response(
                message="Payment not received",
                errors={
                    "type": ErrorTypes.INVALID,
                    "message": payment_message,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # check if order exists
        order = Order.objects.filter(payment_id=payment_id)
        if not order.exists():
            return Response(
                message="Order not found",
                errors={
                    "type": ErrorTypes.NOT_FOUND,
                    "message": "Order not found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        order = order.first()
        # check if order already paid
        if order.status == Order.PAID:
            return Response(
                message="Order already paid",
                errors={
                    "type": ErrorTypes.INVALID,
                    "message": "Order already paid",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # get bill info from moyasar
        try:
            paymenent_details = fetch_payment(payment_id)
        except Exception as e:
            return Response(
                message="Payment failed",
                errors={
                    "type": ErrorTypes.INTERNAL_SERVER_ERROR,
                    "message": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if paymenent_details["status"] != "paid":
            return Response(
                message="Payment not received",
                errors={
                    "type": ErrorTypes.INVALID,
                    "message": "Payment not received",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = Order.PAID
        order.payment_date = timezone.now()
        order.save()

        return Response(
            message="Order paid successfully",
            status=status.HTTP_201_CREATED,
        )


class DisposalCertificateView(APIView):
    permission_classes = [IsBusiness]

    def get(self, request):
        items = OrderItem.objects.filter(
            category__send_certificate=True,order__buyer=self.request.user).order_by('-order__created_at')
        serializer = DisposalCertificateSerializer(items, many=True)

        orderItems = OrderItem.objects.filter(
            category__require_contract=True).order_by('-order__created_at')
        contracts = OrderContractsSerializer(
            orderItems, many=True, context={"request": self.request.user})

        orderItemsreports= OrderItemReport.objects.filter(
            order_item__order__buyer=self.request.user).order_by('-order_item__order__created_at')
        reports=OrderItemReportSerializer(orderItemsreports,many=True)



        data=[*serializer.data,*contracts.data,*reports.data,]


        return Response(message="Items fetched successfully", data={"data":data,"options":[{"choice":"DisposalCertificates","choice_ar": "شهادة إتلاف"},{"choice":"SignedContracts","choice_ar":"عقود موقعة"},{"choice":"Services Reports","choice_ar":"تقارير الخدمات"}]})

class ItemOrderReportListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user
        order_item_reports = OrderItemReport.objects.filter(order_item__order__buyer=user).distinct()
        if not order_item_reports:
            return Response(
                {"message": "No reports found for this user"},
                status=status.HTTP_200_OK
            )
        serializer = OrderItemReportSerializer(order_item_reports, many=True)
        return Response(
            message= "Reports retrieved successfully", 
            data= serializer.data,
            status=status.HTTP_200_OK
        )


class ItemOrderReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,pk):
        order_item_report = OrderItemReport.objects.filter(order_item=pk, order_item__order__buyer=self.request.user)
        print(order_item_report)
        if not order_item_report:
            return Response(
                message="the report has not been uploaded yet",
                status=status.HTTP_404_NOT_FOUND
            )
        serializer= OrderItemReportSerializer(order_item_report)
        return Response(
            message="Order report created successfully",
            status=status.HTTP_200_OK,
            data=serializer.data,
        )

    def post(self,request,pk):
        oredritemID = pk
        try:
            order_item = OrderItem.objects.get(pk=oredritemID, owner=request.user)
        except OrderItem.DoesNotExist:
            return Response(
                message="Order item not found",
                errors={
                    "type": ErrorTypes.NOT_FOUND,
                    "message": "No order item found for this id and user",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        # when the request is for deleting a file, or replacing a file
        if OrderItemReport.objects.filter(order_item=order_item).exists():
            if request.FILES.get("file") is None:
                order_item_report = OrderItemReport.objects.get(order_item=pk, order_item__owner=self.request.user)
                order_item_report.delete()
                return Response(
                message = "Order report deleted successfully",
                status = status.HTTP_204_NO_CONTENT,
                )
            else:
                return Response(
                    message="Order report already exists",
                    errors={
                        "type": ErrorTypes.INVALID,
                        "message": "Order report already exists",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        # if there is no file uploaded then create a row for the file, 
        serializer = OrderItemReportSerializer(data={"report":request.FILES.get("file"),"order_item":pk})
        if not serializer.is_valid():
            return Response(
                message="Validation error",
                errors=serializer.errors,
                serializer=True,
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(
            message="Order report created successfully",
            status=status.HTTP_200_OK, 
            data=serializer.data,
        )
    
    
