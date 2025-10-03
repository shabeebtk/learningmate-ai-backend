from rest_framework import serializers
from learn.models import LearningCategory

class LearningCategorySerializer(serializers.ModelSerializer):
    category_image = serializers.SerializerMethodField()

    class Meta:
        model = LearningCategory
        fields = ['id', 'category', 'category_image', 'description']

    def get_category_image(self, obj):
        if obj.category_image:
            return obj.category_image.url  # full URL from Cloudinary
        return None