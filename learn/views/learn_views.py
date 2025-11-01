import openai
import json
import re
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from accounts.serializers.user_serializers import UserSerializer
from utils.response import response_data
from learn.models import LearningTopic, AIModels, UserLearningHistory, UserTopicStatistics
from learn.serializers.learning_history_serializer import UserLearningHistorySerializer


class GenerateQuestion(APIView):
    permission_classes = []

    def get(self, request, topic_id):
        difficulty = request.query_params.get('difficulty', "easy").lower()

        # Validate topic
        try:
            topic = LearningTopic.objects.get(id=topic_id)
        except LearningTopic.DoesNotExist:
            return response_data(
                success=False,
                message="Topic not found",
            )

        # Validate difficulty
        if difficulty not in ["easy", "medium", "hard"]:
            difficulty = "easy"

        topic_name = topic.topic
        topic_category = topic.category.category
        
        # Get last 5 asked questions for this user and topic to avoid duplicate
        user = request.user if request.user.is_authenticated else None
        asked_questions = []
        if user:
            asked_questions = list(UserLearningHistory.objects.filter(
                user=user,
                topic=topic,
                difficulty=difficulty
            ).order_by('-created_at').values_list("question", flat=True)[:5])

        avoid_text = "\n".join(f"- {q}" for q in asked_questions) if asked_questions else "none"

        prompt = f"""
        You are a friendly mentor. Ask one random theoretical question from the topic "{topic_name}" 
        in the category "{topic_category}" with "{difficulty}" difficulty. 
        Avoid these previously asked questions:
        [{avoid_text}]
        Instructions:
        1. Respond ONLY in JSON format with the following structure:
        {{
            "question": "<the question here as a string and do not put answer here>"
        }}
        2. Do NOT include any text, explanation, code blocks, or extra formatting outside the JSON.
        3. Make the question clear, concise, and suitable for an interview or learning assessment.
        """

        openai.api_key = settings.OPENAI_API_KEY

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful, friendly mentor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )

            gpt_content = response.choices[0].message.content
            gpt_content = re.sub(r"^```json|```$", "", gpt_content.strip(), flags=re.MULTILINE).strip()

            question_json = json.loads(gpt_content)

        except Exception as e:
            return response_data(
                success=False,
                message=f"Failed to generate question: {str(e)}"
            )

        return response_data(success=True, data={"question": question_json})


class AnswerResults(APIView):
    permission_classes = []  # allow both anonymous and authenticated

    def post(self, request):
        user = request.user if request.user.is_authenticated else None
        question = request.data.get('question')
        answer = request.data.get('answer')
        topic_id = request.data.get('topic_id')
        difficulty = request.data.get('difficulty', 'easy').lower()

        if not question or not answer or not topic_id:
            return response_data(
                success=False,
                message="Please provide 'question', 'answer', and 'topic'."
            )

        # Validate topic
        try:
            topic = LearningTopic.objects.get(id=topic_id)
        except Exception as e:
            return response_data(success=False, message="Topic not found")

        # Validate difficulty
        if difficulty not in ['easy', 'medium', 'hard']:
            difficulty = 'easy'
            
        avoid_text = ""
        if user:
            asked_questions = list(UserLearningHistory.objects.filter(
                user=request.user if request.user.is_authenticated else None,
                topic=topic,
                difficulty=difficulty
            ).values_list("question", flat=True))

            avoid_text = "\n".join(f"- {q}" for q in asked_questions[-5:]) if asked_questions else ""
            
        topic_category = topic.category.category

        # Prepare GPT prompt
        prompt = f"""
        Review this answer "{answer}" for question "{question}" (Topic: {topic.topic}, Category: {topic_category}). 
        ignore these already asked questions "[]"
        Instructions:
        - Provide JSON only: {{"feedback": "...", "improved_answer": "...", "score": 0-10}}.
        - Score 10-8: mostly correct, minor gaps. 5-7: partially correct. 1-4: incorrect, - 0: Completely irrelevant or does not attempt to answer.
        - Feedback should be short, friendly, slightly funny.
        - Do not include text outside JSON.
        """

        openai.api_key = settings.OPENAI_API_KEY

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful, friendly mentor and reviewer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )

            gpt_content = response.choices[0].message.content
            gpt_content = re.sub(r"^```json|```$", "", gpt_content.strip(), flags=re.MULTILINE).strip()

            try:
                review_json = json.loads(gpt_content)
            except Exception as e:
                return response_data(
                    success=False,
                    message="failed to get results, please try again",
                    error=f"failed to get expected response - error : {str(e)}"
                )

            # Save user learning history only if authenticated
            if user:
                with transaction.atomic():
                    UserLearningHistory.objects.create(
                        user=user,
                        topic=topic,
                        question=question,
                        difficulty=difficulty,
                        user_answer=answer,
                        feedback=review_json.get("feedback", ""),
                        improved_answer=review_json.get("improved_answer", ""),
                        score=int(review_json.get("score", 0))
                    )
                    # Update or create topic statistics
                    stats, created = UserTopicStatistics.objects.get_or_create(
                        user=user,
                        topic=topic,
                        defaults={"total_score": review_json.get("score", 0), "questions_asked": 1}
                    )
                    if not created:
                        stats.total_score += review_json.get("score", 0)
                        stats.questions_asked += 1
                        stats.save()

        except Exception as e:
            return response_data(
                success=False,
                message=f"Failed to review answer: {str(e)}",
                status_code=500
            )

        # Always return GPT review, regardless of authentication
        return response_data(success=True, data={"review": review_json})
    
    

class ListUserLearningHistory(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, topic_id):
        user = request.user
        limit = int(request.query_params.get("limit") or 50)
        offset = int(request.query_params.get("offset") or 0)
        
        histories = UserLearningHistory.objects.filter(
            user=user, topic=topic_id
        ).order_by("-created_at")
       
        total_count = histories.count()
        paginated = histories[offset:offset+limit]

        serializer = UserLearningHistorySerializer(paginated, many=True)

        return response_data(
            success=True,
            data={
            "count": total_count,
            "next_offset": offset + limit if offset + limit < total_count else None,
            "data": serializer.data
        })