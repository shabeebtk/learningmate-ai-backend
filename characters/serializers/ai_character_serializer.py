from rest_framework import serializers
from characters.models import AICharacter
from learn.serializers.learning_topics_serializers import LearningTopicMiniSerializer

class AiCharacterSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    topic = LearningTopicMiniSerializer(read_only=True)
    
    class Meta:
        model = AICharacter
        fields = [
            'id',
            'name',
            'role',
            'description',
            'avatar',
            'is_active',
            'topic'
        ]
        
    def get_avatar(self, obj):
        return obj.avatar.url if obj.avatar else None