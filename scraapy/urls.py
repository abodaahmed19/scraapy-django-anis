from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from . import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/otp/', include('otp.urls')),
    path('api/', include('pms.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/billing/', include('bms.urls')),
    path('api/document/', include('dms.urls')),
    path('api/driver/', include('driver.urls')),
    path('api/otp/', include('otp.urls')),
    path('api/sms/', include('sms.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
