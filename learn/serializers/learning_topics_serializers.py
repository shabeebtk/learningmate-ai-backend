from rest_framework import serializers
from learn.models import LearningTopic
from learn.serializers.learning_category_serializers import LearningCategorySerializer

class LearningTopicSerializer(serializers.ModelSerializer):
    topic_image = serializers.SerializerMethodField()
    category = LearningCategorySerializer(read_only=True)  # nested category data

    class Meta:
        model = LearningTopic
        fields = ['id', 'topic', 'topic_image', 'description', 'category']

    def get_topic_image(self, obj):
        if obj.topic_image:
            return obj.topic_image.url  # full Cloudinary URL
        return None