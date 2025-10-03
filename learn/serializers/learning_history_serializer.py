from rest_framework import serializers
from learn.models import UserLearningHistory

class UserLearningHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLearningHistory
        fields = [
            "id",
            "question",
            "difficulty",
            "user_answer",
            "feedback",
            "improved_answer",
            "score",
            "created_at",
        ]
