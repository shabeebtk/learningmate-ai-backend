from django.urls import path
from accounts.views.user_auth_views import (
    UserSignupAPIView,
    VerifySignupOTPAPIView,
    UserLoginAPIView,
    ForgotPasswordAPIView,
    ResetPasswordAPIView
)

# base url - /user/

urlpatterns = [
    path('signup', UserSignupAPIView.as_view()),
    path('verify/otp', VerifySignupOTPAPIView.as_view()),
    path('login', UserLoginAPIView.as_view()),
    path('forgot/password', ForgotPasswordAPIView.as_view()),
    path('reset/password', ResetPasswordAPIView.as_view()),
]