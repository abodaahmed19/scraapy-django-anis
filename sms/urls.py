from django.urls import path
from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import ScrapItemCreateAPIView,OrderScrapViewSet

router = DefaultRouter()
router.register(r'orders', OrderScrapViewSet, basename='orders')

urlpatterns = [
    path('create-scrap-item/', ScrapItemCreateAPIView.as_view(), name='create-scrap-item'),
    path('orders/', include(router.urls)),  # Inclure les URLs générées par le router sous /api/orders/
]
