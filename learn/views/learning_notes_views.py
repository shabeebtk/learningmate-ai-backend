import openai
import json
import re
from django.db import transaction
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from utils.response import response_data
from learn.models import UserNotes
from learn.serializers.learning_notes_serializers import UserNotesSerializer


class CreateLearningNote(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        title = request.data.get("title", "")
        content = request.data.get("content", "")
        
        if not title or not content:
            return response_data(
                success=False, 
                message="no content provided",
                status_code=400
            )

        note = UserNotes.objects.create(
            user=user,
            title=title,
            content=content,
        )

        return response_data(
            success=True,
            message="Note created successfully",
            data={
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "created_at": note.created_at
            },
        )
        
        
class ListLearningNotes(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_starred = request.query_params.get("is_starred")

        notes = UserNotes.objects.filter(user=request.user)

        if is_starred is not None:
            notes = notes.filter(is_starred=is_starred.lower() == "true")

        serializer = UserNotesSerializer(notes, many=True)

        return response_data(
            success=True,
            data=serializer.data
        )


class UpdateLearningNote(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, note_id):
        note = UserNotes.objects.filter(
            id=note_id,
            user=request.user
        ).first()

        if not note:
            return response_data(
                success=False,
                message="Note not found",
                status_code=400
            )

        title = request.data.get("title")
        content = request.data.get("content")
        is_starred = request.data.get("is_starred")

        if title is not None:
            note.title = title

        if content is not None:
            note.content = content

        if is_starred is not None:
            note.is_starred = bool(is_starred)

        note.save()

        return response_data(
            success=True,
            message="Note updated successfully",
            data={
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "is_starred": note.is_starred,
                "created_at": note.created_at
            }
        )



class DeleteLearningNote(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, note_id):
        note = UserNotes.objects.filter(
            id=note_id,
            user=request.user
        ).first()

        if not note:
            return response_data(
                success=False,
                message="Note not found",
                status_code=400
            )

        note.delete()

        return response_data(
            success=True,
            message="Note deleted successfully",
            status_code=200
        )