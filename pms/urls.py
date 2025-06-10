from django.urls import path, include, re_path
from knox import views as knox_views
from . import views
from .views import UserMeAPIView


urlpatterns = [
    path("users/token/login/", views.LoginView.as_view(), name="user-login"),
    path("users/token/logout/", knox_views.LogoutView.as_view(), name="knox-logout"),
    path(
        "users/token/logoutall/",
        knox_views.LogoutAllView.as_view(),
        name="knox-logoutall",
    ),
    path(
        "users/activation/",
        views.UserViewSet.as_view({"post": "activation"}),
        name="user-activation",
    ),
    path(
        "users/notifications/",
        views.NotificationView.as_view(),
        name="notification-list",
    ),
    path("users/address/", views.AddressView.as_view(), name="address-list"),
    
    path(
        "users/address/<int:pk>/",
        views.AddressDetailView.as_view(),
        name="address-detail",
    ),
    path(
        "users/business-profile/",
        views.BusinessProfileView.as_view(),
        name="business-profile",
    ),

    
    path('users/me/', views.UserMeAPIView.as_view(), name='user-me'),

    path(
        "users/business-profile/missingdata/",
        views.LegalDataCheckView.as_view(),
        name="missing-data-check",
    ),
    path(
        "users/staff/",
        views.BusinessListApproveView.as_view(),
        name="business-approval-list",
    ),
    path("users/", views.UserCreateView.as_view(), name="user-create"),

    re_path(
        "users/staff/(?P<cr_number>[^/.]+)/approve/",
        views.BusinessDetailApproveView.as_view(),
        name="business-approval-detail",
    ),
    re_path(
        "users/staff/(?P<cr_number>[^/.]+)/reject/",
        views.BusinessDetailRejectView.as_view(),
        name="business-reject-detail",
    ),
    #############################################
    # keep these two urls at the end            #
    #############################################
    re_path(
        "users/social/o/(?P<provider>\S+)/",
        views.LoginSocialView.as_view(),
        name="social-login",
    ),
    #path("", include("djoser.urls")),
]

