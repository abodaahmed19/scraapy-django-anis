from django.urls import path, re_path
from . import views
from .views import FilteredItemListView

urlpatterns = [
    path('home/', views.HomeView.as_view(), name='home'),
    path('categories/', views.CategoryGroupListView.as_view(), name='category-list'),
    path('certificates/', views.CertificateListView.as_view(), name='certificate-list'),
    
    path('items/', views.ItemListView.as_view(), name='item-list'),
    path('items/filter/', views.ItemFilterView.as_view(), name='item-filter'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item-detail'),

    path('user/items/', views.UserItemListView.as_view(), name='user-item-list'),
    path('user/items/item-files/', views.UploadFilesSubItemView.as_view(), name='upload-files-subitem'),
    path('user/items/<int:pk>/', views.UserItemDetailView.as_view(), name='user-item-detail'),
    path('user/items/<int:pk>/images/', views.UserItemImageView.as_view(), name='user-item-image'),
    path('user/items/<int:pk>/images/<int:image_pk>/', views.UserItemImageDetailView.as_view(), name='user-item-image-detail'),
    path('items/filtered/', FilteredItemListView.as_view(), name='filtered-items'),

    path('staff/', views.StaffVendorListView.as_view(), name='staff-vendor-list'),
    re_path('staff/(?P<cr_number>[^/.]+)/items/', views.StaffVendorItemListView.as_view(), name='staff-vendor-item-list'),
    
    path('staff/<int:pk>/approve/', views.ItemDetailApproveView.as_view(), name='item-approval-detail'),
    path('staff/<int:pk>/reject/', views.ItemDetailRejectView.as_view(), name='item-reject-detail'),
    path('staff/category/pending/', views.CategoryListPendingView.as_view(), name='category-list-pending'),
    path('staff/category/approve/<int:pk>/', views.CategoryDetailApproveView.as_view(), name='category-list-approve'),
    path('staff/category/reject/<int:pk>/', views.CategoryDetailRejectView.as_view(), name='category-list-reject'),

    path('staff/vehicle-specs/pending/', views.VehicleSpecsListPendingView.as_view(), name='vehicle-specs-pending-list'),
    path('staff/vehicle-specs/<int:pk>/approve/', views.VehicleSpecsDetailApproveView.as_view(), name='vehicle-specs-approve'),
    path('staff/vehicle-specs/<int:pk>/reject/', views.VehicleSpecsDetailRejectView.as_view(), name='vehicle-specs-reject'),
    # path('user/rental_items/', views.UserRentalItemListView.as_view(), name='user-rental-item-list'),
    # path('user/rental_items/document', views.UserRentalItemListView.as_view(), name='user-rental-item-list'),
]
