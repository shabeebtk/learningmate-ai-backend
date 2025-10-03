from django.db import models
from accounts.models import MyUsers
from cloudinary.models import CloudinaryField
# models here..

class AIModels(models.Model):
    """Stores available AI models (e.g., ChatGPT, Claude..)."""
    name = models.CharField(max_length=100, unique=True, db_index=True)
    label = models.CharField(max_length=100, unique=True, db_index=True)
    
    class Meta:
        verbose_name = "AI Model"
        verbose_name_plural = "AI Models"
        ordering = ["name"]

    def __str__(self):
        return self.name
    

class LearningCategory(models.Model):
    """Represents a learning category (e.g., Programming Languages)."""
    category = models.CharField(max_length=255, unique=True, db_index=True)
    category_image = CloudinaryField('image', folder="categories/", blank=True, null=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Learning Category"
        verbose_name_plural = "Learning Categories"
        ordering = ["category"]

    def __str__(self):
        return self.category


class LearningTopic(models.Model):
    """Represents a topic under a category (e.g., Python under Programming Languages)."""
    category = models.ForeignKey(LearningCategory, on_delete=models.CASCADE,related_name="topics")
    topic = models.CharField(max_length=255, db_index=True)
    topic_image = CloudinaryField('image', folder="topics/", blank=True, null=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Learning Topic"
        verbose_name_plural = "Learning Topics"
        unique_together = ("category", "topic")
        ordering = ["topic"]

    def __str__(self):
        return f"{self.topic} ({self.category.category})"


class UserLearningHistory(models.Model):
    """Tracks user learning attempts for topics."""
    
    DIFFICULTY_EASY = 'easy'
    DIFFICULTY_MEDIUM = 'medium'
    DIFFICULTY_HARD = 'hard'
    DIFFICULTY_CHOICES = [
        (DIFFICULTY_EASY, 'Easy'),
        (DIFFICULTY_MEDIUM, 'Medium'),
        (DIFFICULTY_HARD, 'Hard'),
    ]
    
    user = models.ForeignKey(MyUsers, on_delete=models.CASCADE, related_name="learning_history")
    topic = models.ForeignKey(LearningTopic, on_delete=models.CASCADE, related_name="user_history")
    ai_model = models.ForeignKey(AIModels, on_delete=models.SET_NULL, blank=True, null=True, related_name="histories")
    question = models.TextField()
    difficulty = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES, db_index=True)
    user_answer = models.TextField()
    feedback = models.TextField(null=True, blank=True)
    improved_answer = models.TextField(null=True, blank=True)
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "User Learning History"
        verbose_name_plural = "User Learning Histories"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.topic.topic} ({self.score})"


class UserTopicStatistics(models.Model):
    """Aggregated statistics of a user's performance on a specific topic."""
    user = models.ForeignKey(MyUsers, on_delete=models.CASCADE, related_name="topic_statistics")
    topic = models.ForeignKey(LearningTopic, on_delete=models.CASCADE, related_name="user_statistics")
    total_score = models.IntegerField(default=0)
    questions_asked = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        verbose_name = "User Topic Statistics"
        verbose_name_plural = "User Topic Statistics"
        unique_together = ("user", "topic")
        ordering = ["-total_score"]

    def __str__(self):
        return f"{self.user} - {self.topic.topic}: {self.total_score} points"