from django.conf import settings
from rest_framework.views import APIView
from accounts.models import (
    MyUsers, UserProfile
)
from accounts.serializers.user_serializers import UserSerializer
from utils.response import response_data
from learn.models import LearningCategory
from learn.serializers.learning_category_serializers import LearningCategorySerializer


class ListLearningCategories(APIView):
    permission_classes = []

    def get(self, request):
        search = request.query_params.get("search")
        limit = int(request.query_params.get("limit", 20))   # default 20
        offset = int(request.query_params.get("offset", 0))  # default 0

        queryset = LearningCategory.objects.all().order_by("category")

        if search:
            queryset = queryset.filter(category__icontains=search)

        total_count = queryset.count()
        categories = queryset[offset:offset + limit]

        serializer = LearningCategorySerializer(categories, many=True)

        return response_data(success=True, data={
            "count": total_count,
            "next_offset": offset + limit if offset + limit < total_count else None,
            "data": serializer.data
        })