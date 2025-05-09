# accounts/urls.py

from django.urls import path
from .views import (
    KakaoLoginRedirect, NaverLoginRedirect,
    KakaoLoginCallback, NaverLoginCallback,
    SocialLoginTokenView, LogoutView
)

urlpatterns = [
    path('kakao/login/start/', KakaoLoginRedirect.as_view()),
    path('naver/login/start/', NaverLoginRedirect.as_view()),
    path('kakao/callback/', KakaoLoginCallback.as_view()),
    path('naver/callback/', NaverLoginCallback.as_view()),
    path('social/token/', SocialLoginTokenView.as_view()),
    path('logout/', LogoutView.as_view(), name='custom_logout'),

]
