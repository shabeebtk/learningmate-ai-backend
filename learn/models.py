from django.db import models, transaction
from accounts.models import MyUsers
from cloudinary.models import CloudinaryField
from core.models import BaseUUIDModel
from django.db.models import F

# models here..

class AIModels(BaseUUIDModel):
    """Stores available AI models (e.g., ChatGPT, Claude..)."""
    name = models.CharField(max_length=100, unique=True, db_index=True)
    label = models.CharField(max_length=100, unique=True, db_index=True)
    
    class Meta:
        verbose_name = "AI Model"
        verbose_name_plural = "AI Models"
        ordering = ["name"]

    def __str__(self):
        return self.name
    

class LearningCategory(BaseUUIDModel):
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
    """
    Represents a topic under a category (e.g., Python under Programming Languages).
    """
    category = models.ForeignKey(
        "LearningCategory",
        on_delete=models.CASCADE,
        related_name="topics"
    )
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


class TopicNode(models.Model):
    """
    Represents a node inside a topic.
    Can be Section or Concept.
    """

    LEVEL_SECTION = "section"
    LEVEL_CONCEPT = "concept"

    LEVEL_CHOICES = [
        (LEVEL_SECTION, "Section"),
        (LEVEL_CONCEPT, "Concept"),
    ]

    topic = models.ForeignKey(
        LearningTopic,
        on_delete=models.CASCADE,
        related_name="nodes"
    )

    name = models.CharField(max_length=255, db_index=True)

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children"
    )

    level = models.CharField(
        max_length=30,
        choices=LEVEL_CHOICES,
        db_index=True
    )

    description = models.TextField(blank=True)

    order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        with transaction.atomic():

            if self.pk:
                old = TopicNode.objects.get(pk=self.pk)

                # If parent changed → fix old siblings first
                if old.parent != self.parent:
                    TopicNode.objects.filter(
                        topic=old.topic,
                        parent=old.parent,
                        order__gt=old.order
                    ).update(order=F("order") - 1)

                    # reset order for new group
                    self.pk = None

            if self.pk is None:
                siblings = TopicNode.objects.filter(
                    topic=self.topic,
                    parent=self.parent
                )

                if self.order == 0:
                    max_order = siblings.aggregate(
                        models.Max("order")
                    )["order__max"] or 0

                    self.order = max_order + 1
                else:
                    siblings.filter(
                        order__gte=self.order
                    ).update(order=F("order") + 1)

            else:
                old = TopicNode.objects.get(pk=self.pk)

                if old.order != self.order:
                    siblings = TopicNode.objects.filter(
                        topic=self.topic,
                        parent=self.parent
                    ).exclude(pk=self.pk)

                    if self.order > old.order:
                        siblings.filter(
                            order__gt=old.order,
                            order__lte=self.order
                        ).update(order=F("order") - 1)
                    else:
                        siblings.filter(
                            order__lt=old.order,
                            order__gte=self.order
                        ).update(order=F("order") + 1)

            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():

            siblings = TopicNode.objects.filter(
                topic=self.topic,
                parent=self.parent,
                order__gt=self.order
            )

            # Shift remaining siblings up
            siblings.update(order=F("order") - 1)

            super().delete(*args, **kwargs)

    class Meta:
        ordering = ["order"]
        unique_together = ("topic", "parent", "order")


class UserLearningHistory(BaseUUIDModel):
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


class UserTopicStatistics(BaseUUIDModel):
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
    
    
class UserNotes(BaseUUIDModel):
    user = models.ForeignKey(MyUsers, on_delete=models.CASCADE, related_name="notes")
    title = models.CharField(max_length=255, db_index=True)
    content = models.TextField(null=True, blank=True) 
    is_starred = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.title}"
