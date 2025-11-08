import openai
import re, json
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from accounts.serializers.user_serializers import UserSerializer
from utils.response import response_data
from django.conf import settings
from django.db import transaction
from characters.models import (
    AICharacter, AIChatMemory, AICharacterChatMessages
)
from characters.serializers.ai_character_chat_serializer import UserAiChatsSerializer


class ListUserAiChats(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, character_id):
        user = request.user
        limit = int(request.query_params.get("limit", 20))
        offset = int(request.query_params.get("offset", 0))

        # Get all chat messages between user and the AI character
        messages_qs = (
            AICharacterChatMessages.objects
            .filter(user=user, ai_character_id=character_id)
            .select_related('ai_character')
            .order_by('-created_at')  # newest first for pagination
        )

        total_count = messages_qs.count()
        paginated_messages = messages_qs[offset:offset + limit]
        
        # reverse them before sending to display oldest-first in chat window
        serializer = UserAiChatsSerializer(reversed(paginated_messages), many=True)

        return response_data(success=True, data={
            "count": total_count,
            "next_offset": offset + limit if offset + limit < total_count else None,
            "data": serializer.data
        })


class ChatWithAICharacter(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        character_id = request.data.get("character_id")
        user_message = request.data.get("message")

        if not character_id or not user_message:
            return response_data(success=False, message="character_id and message are required", status_code=400)

        ai_character = (
            AICharacter.objects.filter(id=character_id, is_active=True)
            .select_related("topic")
            .first()
        )
        if not ai_character:
            return response_data(success=False, message="AI character not found", status_code=404)

        memory, _ = AIChatMemory.objects.get_or_create(
            user=user,
            ai_character=ai_character,
            defaults={"summary": ""}
        )

        # --- Fetch clean recent messages for context ---
        recent_messages = (
            AICharacterChatMessages.objects
            .filter(user=user, ai_character=ai_character)
            .exclude(message__exact="")  # skip empty messages
            .order_by("-created_at")[:4]
        )
        recent_messages = reversed(recent_messages)  # chronological order

        chat_history = []
        for msg in recent_messages:
            role = "user" if msg.sender == AICharacterChatMessages.SENDER_USER else "assistant"
            chat_history.append({"role": role, "content": msg.message})

        personality_str = (
            ", ".join([f"{k}: {v}" for k, v in ai_character.personality.items()])
            if ai_character.personality else "N/A"
        )

        # --- Stronger prompt for continuity ---
        if ai_character.role == AICharacter.AI_ROLE_FRIEND:
            system_prompt = f"""
            always give response and summary strictly in JSON:
            {{
            "response": "<your message to the user>",
            "summary": "<updated long-term summary reflecting this and past chats>"
            }}
            
            Rules:
            - No markdown, no code fences.
            - Keep messages short and natural.
            
            You name is {ai_character.name}, a Friend companion chatting with {user.profile.name or user.username}.
            "Topic": "{ai_character.topic.topic}",
            "Personality": "{personality_str}",
            "chat previous summary": "{memory.summary or 'None'}".
            """
        else:
            system_prompt = f"""
            always give response and summary strictly in JSON:
            {{
            "response": "<your message to the user>",
            "summary": "<updated long-term summary reflecting this and past chats>"
            }}
            
            Rules:
            - No markdown, no code fences.
            - Keep messages short and natural.
            
            Your name is "{ai_character.name}", a mentor guiding username:"{user.profile.name or user.username}" in "{ai_character.topic.topic}".
            "your Personality" : "{personality_str}",
            "chat Previous summary": "{memory.summary or 'None'}".
            """

        # --- Build and send messages ---
        openai.api_key = settings.OPENAI_API_KEY

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})

        print("messages:", messages)

        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=400
        )

        ai_output = completion.choices[0].message.content.strip()
        print("[AI OUTPUT] :", ai_output)
        
        print()
        print('-----------')

        # --- Extract sections robustly ---
        response_text, summary_update = self.extract_ai_json_response(ai_output)
        
        print('-response ---', response_text)
        print()
        print()
        print('-summary ---', summary_update)

        with transaction.atomic():
            AICharacterChatMessages.objects.create(
                user=user,
                ai_character=ai_character,
                sender=AICharacterChatMessages.SENDER_USER,
                message=user_message,
            )
            AICharacterChatMessages.objects.create(
                user=user,
                ai_character=ai_character,
                sender=AICharacterChatMessages.SENDER_AI,
                message=response_text,
            )

            if summary_update:
                memory.summary = (memory.summary.strip() + " " + summary_update).strip()
                memory.save(update_fields=["summary", "updated_at"])

        return response_data(success=True, data={"response": response_text})


    def extract_ai_json_response(self, ai_output: str):
        """
        Safely extracts structured JSON data from AI response.

        The model is expected to return:
        {
        "response": "<assistant message>",
        "summary": "<updated memory summary>"
        }

        This helper:
        - Removes unwanted Markdown code fences.
        - Attempts to parse JSON.
        - Falls back gracefully if parsing fails.

        Returns:
            tuple: (response_text, summary_text)
        """
        if not ai_output:
            return "", ""

        # Clean any Markdown JSON fences
        ai_output_clean = re.sub(r"^```json|```$", "", ai_output.strip(), flags=re.MULTILINE).strip()

        try:
            data = json.loads(ai_output_clean)
            response_text = str(data.get("response", "")).strip()
            summary_text = str(data.get("summary", "")).strip()
            return response_text, summary_text
        except Exception as e:
            # Try to extract manually if model output contains partial JSON
            # Minimal fallback parsing
            response_text, summary_text = "", ""
            if '"response"' in ai_output_clean:
                match = re.search(r'"response"\s*:\s*"([^"]+)"', ai_output_clean)
                if match:
                    response_text = match.group(1).strip()

            if '"summary"' in ai_output_clean:
                match = re.search(r'"summary"\s*:\s*"([^"]+)"', ai_output_clean)
                if match:
                    summary_text = match.group(1).strip()

            # Fallback to full text if still empty
            if not response_text and not summary_text:
                response_text = ai_output_clean

            return response_text, summary_text
