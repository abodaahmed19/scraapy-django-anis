from django.urls import path
from .views import SendOTPView, xVerifyOTPView,LoginOTPView,ResendOTPView,VerifOTPWithTokenView

urlpatterns = [
    path('login/',   LoginOTPView.as_view(),   name='login-otp'),
    path('send/',   SendOTPView.as_view(),   name='send-otp'),
    path('verify/', xVerifyOTPView.as_view(), name='verify-otp'),
    path('resend/', ResendOTPView.as_view(), name='resend-otp'),
    path('verify-otp-token/', VerifOTPWithTokenView.as_view(), name='verify-otp-token'),

]


