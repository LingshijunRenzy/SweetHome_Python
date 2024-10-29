from rest_framework.permissions import BasePermission

class IsStaffOrAuthor(BasePermission):
    """
    仅允许管理员或作者访问
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        return obj.author == request.user