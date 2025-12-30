from rest_framework import serializers
from learn.models import UserNotes


class UserNotesSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserNotes
        fields = ['id', 'title', 'content', 'is_starred', 'created_at']