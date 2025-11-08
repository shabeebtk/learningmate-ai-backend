from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from accounts.serializers.user_serializers import UserSerializer
from utils.response import response_data
from django.shortcuts import get_object_or_404
from characters.models import (
    AICharacter
)
from characters.serializers.ai_character_serializer import AiCharacterSerializer


class ListAiCharacters(APIView):

    def get(self, request):
        search = request.query_params.get("search")
        topic_id = request.query_params.get("topic_id")
        role = request.query_params.get("role")
        limit = int(request.query_params.get("limit", 20))   # default 20
        offset = int(request.query_params.get("offset", 0))  # default 0

        queryset = AICharacter.objects.filter(is_active=True).order_by("name")

        # Filtering
        if search:
            queryset = queryset.filter(name__icontains=search)
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        if role:
            queryset = queryset.filter(role=role)

        # Pagination
        total_count = queryset.count()
        characters = queryset[offset:offset + limit]

        serializer = AiCharacterSerializer(characters, many=True)

        return response_data(success=True, data={
            "count": total_count,
            "next_offset": offset + limit if offset + limit < total_count else None,
            "data": serializer.data
        })


class GetAiCharacterDetails(APIView):

    def get(self, request, character_id):
        # Use select_related for performance (fetch topic in same query)
        ai_character = get_object_or_404(
            AICharacter.objects.select_related("topic"),
            id=character_id,
            is_active=True
        )

        serializer = AiCharacterSerializer(ai_character)
        return response_data(success=True, data={"character": serializer.data})

