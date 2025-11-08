from rest_framework import serializers
from characters.models import AICharacterChatMessages, AICharacter
from characters.serializers.ai_character_serializer import AiCharacterSerializer




class UserAiChatsSerializer(serializers.ModelSerializer):

    class Meta:
        model = AICharacterChatMessages
        fields = '__all__'