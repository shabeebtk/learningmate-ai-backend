from rest_framework import serializers
from characters.models import AICharacterChatMessages, AICharacter


class UserAiChatsSerializer(serializers.ModelSerializer):

    class Meta:
        model = AICharacterChatMessages
        fields = '__all__'