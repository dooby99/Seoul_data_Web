import os
import requests
import secrets

from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

# --- 리다이렉트용: 소셜 로그인 화면 이동 ---
class KakaoLoginRedirect(APIView):
    def get(self, request):
        client_id = os.getenv('KAKAO_CLIENT_ID')
        if not client_id:
            raise ImproperlyConfigured("KAKAO_CLIENT_ID가 없습니다.")
        redirect_uri = 'http://13.209.241.181:8000/api/accounts/kakao/callback/'
        auth_url = (
            f"https://kauth.kakao.com/oauth/authorize"
            f"?response_type=code"
            f"&client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
        )
        return redirect(auth_url)

class NaverLoginRedirect(APIView):
    def get(self, request):
        client_id = os.getenv('NAVER_CLIENT_ID')
        if not client_id:
            raise ImproperlyConfigured("NAVER_CLIENT_ID가 없습니다.")

        redirect_uri = 'http://13.209.241.181:8000/api/accounts/naver/callback/'
        state = secrets.token_urlsafe(16)
        request.session['naver_state'] = state   

        auth_url = (
            f"https://nid.naver.com/oauth2.0/authorize"
            f"?response_type=code"
            f"&client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
        )
        return redirect(auth_url)

# --- 콜백 처리용: code만 넘김 ---
class KakaoLoginCallback(APIView):
    def get(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({"error": "No code provided"}, status=400)

        # 프론트엔드로 code만 전달
        frontend_redirect_url = f"http://13.209.241.181:3000/login/success?provider=kakao&code={code}"
        return redirect(frontend_redirect_url)

class NaverLoginCallback(APIView):
    def get(self, request):
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        session_state = request.session.get('naver_state')

        if not code or not state:
            return Response({"error": "Missing code or state"}, status=400)

        if state != session_state:
            return Response({"error": "Invalid state"}, status=400)

        frontend_redirect_url = f"http://13.209.241.181:3000/login/success?provider=naver&code={code}&state={state}"

        return redirect(frontend_redirect_url)

# --- 실제 토큰 발급 API ---
class SocialLoginTokenView(APIView):
    def post(self, request):
        provider = request.data.get('provider')
        code = request.data.get('code')
        state = request.data.get('state', '')

        if not provider or not code:
            return Response({"error": "Missing provider or code"}, status=400)

        if provider == 'kakao':
            token_url = "https://kauth.kakao.com/oauth/token"
            payload = {
                "grant_type": "authorization_code",
                "client_id": os.getenv("KAKAO_CLIENT_ID"),
                "client_secret": os.getenv("KAKAO_CLIENT_SECRET"),
                "redirect_uri": "http://13.209.241.181:8000/api/accounts/kakao/callback/",
                "code": code,
            }
            user_info_url = "https://kapi.kakao.com/v2/user/me"
            
        elif provider == 'naver':
            token_url = "https://nid.naver.com/oauth2.0/token"
            payload = {
                "grant_type": "authorization_code",
                "client_id": os.getenv("NAVER_CLIENT_ID"),
                "client_secret": os.getenv("NAVER_CLIENT_SECRET"),
                "redirect_uri": "http://13.209.241.181:8000/api/accounts/naver/callback/",
                "code": code,
                "state": state,
            }
            user_info_url = "https://openapi.naver.com/v1/nid/me"
        else:
            return Response({"error": "Unsupported provider"}, status=400)

        try:
            token_res = requests.post(token_url, data=payload)
            token_res.raise_for_status()
            access_token = token_res.json().get("access_token")
        except requests.RequestException as e:
            return Response({"error": str(e)}, status=400)

        try:
            user_info_res = requests.get(
                user_info_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_info_res.raise_for_status()
        except requests.RequestException as e:
            return Response({"error": str(e)}, status=400)

        user_info = user_info_res.json()

        if provider == 'kakao':
            kakao_id = user_info["id"]
            nickname = user_info["properties"].get("nickname", f"kakao_{kakao_id}")
            username = f"kakao_{kakao_id}"
        else:  # naver
            naver_id = user_info["response"]["id"]
            nickname = user_info["response"].get("nickname", f"naver_{naver_id}")
            username = f"naver_{naver_id}"

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"first_name": nickname}
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=200)
