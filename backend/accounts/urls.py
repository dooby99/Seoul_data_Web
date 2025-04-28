from django.urls import path
from .views import (
    KakaoLoginRedirect, NaverLoginRedirect,
    KakaoLoginCallback, NaverLoginCallback,
    SocialLoginTokenView
)

urlpatterns = [
    path('kakao/login/start/', KakaoLoginRedirect.as_view()),
    path('naver/login/start/', NaverLoginRedirect.as_view()),
    path('kakao/callback/', KakaoLoginCallback.as_view()),
    path('naver/callback/', NaverLoginCallback.as_view()),
    path('social/token/', SocialLoginTokenView.as_view()),
]
