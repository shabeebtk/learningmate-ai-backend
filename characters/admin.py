from django.contrib import admin
from characters.models import AICharacter, AICharacterChatMessages, AIChatMemory
# Register your models here.

admin.site.register(AICharacter)
admin.site.register(AICharacterChatMessages)
admin.site.register(AIChatMemory)