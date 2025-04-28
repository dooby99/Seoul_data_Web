from xml.etree.ElementInclude import include

from django.contrib import admin
from django.urls import path, include
from dj_rest_auth.views import UserDetailsView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('recommend.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/accounts/user/', UserDetailsView.as_view(), name='user_detail'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/board/', include('board.urls')),

]
