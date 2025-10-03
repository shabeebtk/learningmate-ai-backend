from rest_framework.views import APIView
from accounts.models import (
    MyUsers, UserProfile
)
from rest_framework.permissions import IsAuthenticated
from accounts.serializers.user_serializers import UserSerializer
from utils.response import response_data


class GetUserDetails(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user_data = UserSerializer(request.user).data
        
        return response_data(
            success=True,
            data=user_data
        )