from django.urls import path
from characters.views.ai_character_views import (
    ListAiCharacters, GetAiCharacterDetails
)
from characters.views.ai_character_chat_views import (
    ListUserAiChats, ChatWithAICharacter
)

# base url - /ai-characters/

urlpatterns = [
    path('list', ListAiCharacters.as_view()),
    path('<int:character_id>/details', GetAiCharacterDetails.as_view()),
    
    path('chat', ChatWithAICharacter.as_view()),
    path('<int:character_id>/chat/messages', ListUserAiChats.as_view()),
]
