from django.urls import path
from .views import (
DeleteDriverView,
UserDriverView,
DriverRenewPasswordView,
DriverOrderDeliveryRequest

)

urlpatterns = [
    # path("", BillList.as_view(), name="bill-list"),
    path("create/", UserDriverView.as_view(), name="create-driver"),
    path('<int:pk>/', DeleteDriverView.as_view(), name='delete-driver'),
    path("renew-password/", DriverRenewPasswordView.as_view(), name="renew-password"),
    path("list/", DriverOrderDeliveryRequest.as_view(), name="driver-order-delivery-request"),
]