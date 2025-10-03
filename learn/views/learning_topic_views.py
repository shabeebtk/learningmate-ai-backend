from django.conf import settings
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from utils.response import response_data
from learn.models import LearningTopic, UserTopicStatistics
from learn.serializers.learning_topics_serializers import LearningTopicSerializer

# views 
class ListLearningTopics(APIView):
    permission_classes = []

    def get(self, request):
        search = request.query_params.get("search")
        category = request.query_params.get("category")
        limit = int(request.query_params.get("limit", 20))   # default 20
        offset = int(request.query_params.get("offset", 0))  # default 0

        queryset = LearningTopic.objects.all().order_by("topic")

        if search:
            queryset = queryset.filter(topic__icontains=search)
            
        if category:
            queryset = queryset.filter(category__category=category)

        total_count = queryset.count()
        topics = queryset[offset:offset + limit]

        serializer = LearningTopicSerializer(topics, many=True)

        return response_data(success=True, data={
            "count": total_count,
            "next_offset": offset + limit if offset + limit < total_count else None,
            "data": serializer.data
        })
        
        

class TopicDetailView(APIView):
    permission_classes = []

    def get(self, request, topic_id):
        # Fetch topic
        topic = get_object_or_404(LearningTopic, id=topic_id)
        user = request.user if request.user.is_authenticated else None

        # Topic basic info
        topic_data = LearningTopicSerializer(topic).data

        # User-specific statistics
        if user:
            stats = UserTopicStatistics.objects.filter(user=user, topic=topic).first()
            topic_data["user_statistics"] = {
                "total_score": stats.total_score if stats else 0,
                "questions_asked": stats.questions_asked if stats else 0
            }

        return response_data(success=True, data=topic_data)