# accounts/views.py

from allauth.socialaccount.providers.kakao.views import KakaoOAuth2Adapter
from allauth.socialaccount.providers.naver.views import NaverOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


class NaverLogin(SocialLoginView):
    adapter_class = NaverOAuth2Adapter

    def get_response(self):
        response = super().get_response()
        user = self.user

        # JWT 토큰 발급
        refresh = RefreshToken.for_user(user)
        jwt_data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        # 최종 응답 바꿔치기
        response.data = jwt_data
        return response

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class KakaoLogin(SocialLoginView):
    adapter_class = KakaoOAuth2Adapter

    def get_response(self):
        response = super().get_response()
        user = self.user

        # JWT 토큰 발급
        refresh = RefreshToken.for_user(user)
        jwt_data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        response.data = jwt_data
        return response