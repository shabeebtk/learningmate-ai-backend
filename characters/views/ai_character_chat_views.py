import openai
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
            .order_by('created_at')  # newest first for pagination
        )

        total_count = messages_qs.count()
        paginated_messages = messages_qs[offset:offset + limit]

        # Use serializer to return data
        serializer = UserAiChatsSerializer(paginated_messages, many=True)

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

        # Get the AI character
        ai_character = AICharacter.objects.filter(id=character_id, is_active=True).select_related("topic").first()
        if not ai_character:
            return response_data(success=False, message="AI character not found", status_code=404)

        # Get or create memory for this user-character pair
        memory, _ = AIChatMemory.objects.get_or_create(
            user=user,
            ai_character=ai_character,
            defaults={"summary": ""}
        )

        # Get personality as string (if JSON)
        personality_str = ", ".join([f"{k}: {v}" for k, v in ai_character.personality.items()]) if ai_character.personality else "N/A"

        # Prepare dynamic prompt based on role
        if ai_character.role == AICharacter.AI_ROLE_FRIEND:
            prompt = f"""
            You are {ai_character.name}, a friendly AI friend chatting with {user.profile.name or user.username}. 
            Your topic of focus is {ai_character.topic.topic}.
            Previous summary: "{memory.summary}"
            Your personality: {personality_str}

            Guidelines:
            - Act natural and empathetic.
            - Keep it short and friendly.
            - Remember past chats naturally.

            Respond in this format:
            ### Response:
            <your message>

            ### Summary:
            <updated summary>
            """
        else:
            prompt = f"""
            You are {ai_character.name}, a kind and encouraging mentor guiding {user.profile.name or user.username} in {ai_character.topic.topic}.
            Previous summary: "{memory.summary}"
            Your personality: {personality_str}

            Guidelines:
            - Teach gently and motivate.
            - Use practical examples.
            - Keep responses short and professional.

            Respond in this format:
            ### Response:
            <your message>

            ### Summary:
            <updated summary>
            """

        # --- Call OpenAI API ---
        openai.api_key = settings.OPENAI_API_KEY
        
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.8,
        )
        
        print(completion)

        ai_output = completion.choices[0].message.content
        
        print('[AI] ; ', ai_output)

        # Extract response and summary parts
        response_text, summary_update = self._extract_response_and_summary(ai_output)

        # --- Save chat and memory updates ---
        with transaction.atomic():
            # Save user message
            AICharacterChatMessages.objects.create(
                user=user,
                ai_character=ai_character,
                sender=AICharacterChatMessages.SENDER_USER,
                message=user_message
            )

            # Save AI response
            AICharacterChatMessages.objects.create(
                user=user,
                ai_character=ai_character,
                sender=AICharacterChatMessages.SENDER_AI,
                message=response_text
            )

            # Update memory summary
            new_summary = f"{memory.summary.strip()} {summary_update}".strip()
            memory.summary = new_summary
            memory.save(update_fields=["summary", "updated_at"])

        return response_data(success=True, data={
            "response": response_text,
        })

    def _extract_response_and_summary(self, ai_output: str):
        """Parse AI output format."""
        response_part = ""
        summary_part = ""
        lines = ai_output.splitlines()
        current = None

        for line in lines:
            if line.strip().startswith("### Response:"):
                current = "response"
                continue
            elif line.strip().startswith("### Summary:"):
                current = "summary"
                continue

            if current == "response":
                response_part += line + "\n"
            elif current == "summary":
                summary_part += line + "\n"

        return response_part.strip(), summary_part.strip()