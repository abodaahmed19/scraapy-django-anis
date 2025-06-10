from rest_framework.permissions import BasePermission


class IsBusiness(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_business


class IsBusinessComplete(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_business and hasattr(request.user, 'business_profile')


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_staff
    
class IsDriver(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated or not request.user.user_type == "driver":
            return False
        return True
    
class IsBusinessOrIsStaff(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and (
                hasattr(request.user, 'business_profile') or
                request.user.is_staff
            )
        )