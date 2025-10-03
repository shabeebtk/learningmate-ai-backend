import random
import string
import requests
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.conf import settings
from rest_framework.views import APIView
from accounts.models import (
    MyUsers, UserProfile
)
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.serializers.user_serializers import UserSerializer
from utils.response import response_data

GOOGLE_AUTH_URL='https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL='https://oauth2.googleapis.com/token'
GOOGLE_USER_INFO_URL='https://www.googleapis.com/oauth2/v2/userinfo'


class GoogleLoginUrlView(APIView):
    """
    generates a Google OAuth2 login URL 
    """

    def get(self, request):        
        # Build the Google OAuth2 authorization URL
        auth_url = (
            f"{GOOGLE_AUTH_URL}?response_type=code"
            f"&client_id={settings.GOOGLE_AUTH_CLIENT_ID}"
            f"&redirect_uri={settings.GOOGLE_CALLBACK_URI}"
            f"&scope={settings.GOOGLE_AUTH_SCOPE}"
            f"&access_type=offline"
            f"&prompt=consent"
        )
        data = {
            "auth_url": auth_url
        }
        return response_data(success=True, data=data)
        

class GoogleAuthCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.query_params.get("code")
        if not code:
            return response_data(
                success=False,
                message="Authorization code is required",
                status_code=400
            )

        try:
            # 1. Exchange code for access token
            token_data = {
                "code": code,
                "client_id": settings.GOOGLE_AUTH_CLIENT_ID,
                "client_secret": settings.GOOGLE_AUTH_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_CALLBACK_URI,
                "grant_type": "authorization_code",
            }
            token_res = requests.post(GOOGLE_TOKEN_URL, data=token_data)
            token_res.raise_for_status()
            token_json = token_res.json()

            access_token = token_json.get("access_token")
            
            print(access_token)
            
            if not access_token:
                return response_data(
                    success=False,
                    message="Failed to login through google",
                    error="no access token from google",
                    status_code=400
                )

            # 2. Fetch user info from Google
            userinfo_res = requests.get(
                GOOGLE_USER_INFO_URL, headers={"Authorization": f"Bearer {access_token}"}
            )
            
            print(userinfo_res.text)
            
            userinfo_res.raise_for_status()
            userinfo = userinfo_res.json()
            
            print(userinfo, '----')

            email = userinfo.get("email")

            if not email:
                return response_data(
                    success=False,
                    message="failed to login with Google account",
                    error=f"failed to login with Google account email not available. email : {email}",
                    status_code=400
                )
            name = userinfo.get("name") or email.split("@")[0]

            # 3. Create or get user
            with transaction.atomic():
                user, created = MyUsers.objects.get_or_create(
                    email=email,
                    defaults={
                        "username": email.split("@")[0],
                        "password": make_password(
                            "".join(random.choices(string.ascii_letters + string.digits, k=12))
                        ),
                        "is_verified": True,  # auto verified since Google verified
                    },
                )

                # get or create profile
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        "name": name
                    }
                )

            # 4. Issue JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            user_data = UserSerializer(user).data

            return response_data(
                success=True,
                message="login successful",
                data={
                    "access": access_token,
                    "refresh": str(refresh),
                    "user": user_data,
                },
                status_code=200
            )

        except requests.exceptions.RequestException as e:
            return response_data(
                success=False,
                message="Google authentication failed",
                status_code=400,
                error=str(e)
            )
        except Exception as e:
            return response_data(
                success=False,
                message="Internal server error",
                status_code=500,
                error=str(e)
            )