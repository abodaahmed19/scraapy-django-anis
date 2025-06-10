from django.contrib import admin
from .models import Order,OrderItem,OrderTracking,CategoryShippingRate,OrderItemReport,TrackingSystemAddresses
from driver.models import DriverOrderTracking


# Register your models here.
# class InvoiceItemAdmin(admin.TabularInline):
#     model = InvoiceItem
#     extra = 0

# @admin.register(Bill)
# class BillAdmin(admin.ModelAdmin):
#     inlines = [InvoiceItemAdmin,]
#     list_display = ('id', 'type', 'category', 'total_price')
#     list_filter = ('type', 'category')
#     search_fields =  ('type', 'category')
#     list_display_links = ('id', 'type', 'category')

@admin.register(CategoryShippingRate)
class CategoryShippingRateAdmin(admin.ModelAdmin):
    list_display = ('category', 'rate_per_km')
    search_fields = ('category__name',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'total_price']
    list_filter = ['id', 'status']
    search_fields = ['id', 'status']

admin.site.register(OrderItem)


admin.site.register(OrderTracking)

admin.site.register(OrderItemReport)

admin.site.register(TrackingSystemAddresses)

admin.site.register(DriverOrderTracking)
