from rest_framework.throttling import UserRateThrottle

class VerifyOTPThrottle(UserRateThrottle):
    scope = 'verify_otp'
