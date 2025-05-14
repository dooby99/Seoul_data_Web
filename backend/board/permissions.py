from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    작성자만 수정/삭제할 수 있고, 그 외 사용자는 읽기만 허용
    """
    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS (GET, HEAD, OPTIONS)은 모두 허용
        if request.method in permissions.SAFE_METHODS:
            return True
        # 작성자만 PUT, PATCH, DELETE 허용
        return obj.author == request.user
