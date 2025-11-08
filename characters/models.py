from django.db import models
from learn.models import LearningTopic
from cloudinary.models import CloudinaryField
from accounts.models import MyUsers

# Create your models here.

'''

{
  "id": 2,
  "name": "Lex",
  "role": "AI Buddy",
  "description": "A fun, enthusiastic coding companion who learns alongside the user. Encourages exploration, experimentation, and curiosity with light humor and empathy.",
  "personality": {
    "tone": "friendly",


'''

class AICharacter(models.Model):
    AI_ROLE_FRIEND = 'friend'
    AI_ROLE_MENTOR = 'mentor'
    
    AI_ROLES_CHOICES = [
        (AI_ROLE_FRIEND, "Friend"),
        (AI_ROLE_MENTOR, "Mentor"),
    ]
    
    name = models.CharField(max_length=100)
    topic = models.ForeignKey(LearningTopic, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=AI_ROLES_CHOICES)  # e.g. "Mentor", "Buddy"
    description = models.TextField(blank=True, null=True)
    personality = models.JSONField(default=dict, blank=True, null=True)
    avatar = CloudinaryField('image', folder="ai_characters/avatar/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "AI Character"
        verbose_name_plural = "AI Characters"
        
        indexes = [
            models.Index(fields=["topic"]),
            models.Index(fields=["role"]),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.role})  --> topic : {self.topic.topic if self.topic else "no topic selected"}"
    
    
class AICharacterChatMessages(models.Model):
    SENDER_USER = 'user'
    SENDER_AI = 'ai'

    SENDER_CHOICES = [
        (SENDER_USER, 'User'),
        (SENDER_AI, 'AI'),
    ]

    user = models.ForeignKey(MyUsers, on_delete=models.CASCADE, related_name="chat_messages")
    ai_character = models.ForeignKey(AICharacter, on_delete=models.SET_NULL, null=True, related_name="ai_chat_messages")
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "AI Character Chat Message"
        verbose_name_plural = "AI Character Chat Messages"
        indexes = [
            models.Index(fields=["user", "ai_character"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.sender.upper()} - {self.message[:40]}..."

    

class AIChatMemory(models.Model):
    user = models.ForeignKey(MyUsers, on_delete=models.CASCADE)
    ai_character = models.ForeignKey(AICharacter, on_delete=models.SET_NULL, null=True)
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Character Chat memory"
        verbose_name_plural = "AI Character Chats Memories"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "ai_character"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Chat with {self.ai_character} by {self.user}"
