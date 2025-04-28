from django.urls import path, include
from .views import NaverLogin, LogoutView, KakaoLogin


urlpatterns = [
    path('naver/login/', NaverLogin.as_view(), name='naver_login'),
    path('kakao/login/', KakaoLogin.as_view(), name='kakao_login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
