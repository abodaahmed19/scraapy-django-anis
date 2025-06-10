from django.urls import path
from .views import (
    BillList,
    BillDetail,
    CheckOutSuggestion,
    OrderListView,
    OrderDetailView,
    PaymentCallbackView,
    DisposalCertificateView,
    ItemOrderReportView,
    ItemOrderReportListView
)

urlpatterns = [
    path("", BillList.as_view(), name="bill-list"),
    path("<uuid:pk>/", BillDetail.as_view(), name="bill-detail"),
    path( 
        "checkout/geo/",
        CheckOutSuggestion.as_view(),
        name="checkout-additional-services",
    ),
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/<uuid:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("orderitem/reports/",ItemOrderReportListView.as_view(), name="user-order-reports"),
    path("orderitem/report/<int:pk>/", ItemOrderReportView.as_view(), name="order-report"),
    path(
        "payment/callback/",
        PaymentCallbackView.as_view(),
        name="payment-callback",
    ),
    path(
        "disposal-certificate/",
        DisposalCertificateView.as_view(),
        name="disposal-certificate",
    ),
    # path('create/', BillCreate.as_view(), name='bill-create'),
    # path('choices/', BillChoices.as_view(), name='bill-choices'),
]
