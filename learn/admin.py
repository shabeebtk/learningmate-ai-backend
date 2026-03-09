from django.contrib import admin
from learn.models import (
    AIModels, LearningCategory, LearningTopic, TopicNode, UserLearningHistory, AssessmentQuestion, 
    AssessmentAnswer, UserAssessments
)
# Register your models here.


admin.site.register(AIModels)
@admin.register(LearningCategory)
class LearningCategoryAdmin(admin.ModelAdmin):
    list_display = ("category",)
    search_fields = ("category",)
    ordering = ("category",)
    
    

@admin.register(LearningTopic)
class LearningTopicAdmin(admin.ModelAdmin):
    list_display = ("topic", "category")
    list_filter = ("category",)
    search_fields = ("topic", "category__category")
    ordering = ("category", "topic")


@admin.register(TopicNode)
class TopicNodeAdmin(admin.ModelAdmin):
    list_display = ("indented_name", "topic", "level", "order", "is_active")
    list_filter = ("topic", "level", "is_active")
    search_fields = ("name", "topic__topic")
    ordering = ("topic", "parent", "order")

    autocomplete_fields = ("topic", "parent")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("parent", "topic")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent":
            kwargs["queryset"] = TopicNode.objects.filter(
                level=TopicNode.LEVEL_SECTION
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def indented_name(self, obj):
        indent = ""
        current = obj.parent
        while current:
            indent += "— "
            current = current.parent
        return f"{indent}{obj.name}"

    indented_name.short_description = "Name"


admin.site.register(UserLearningHistory)

class AssessmentAnswerInline(admin.TabularInline):
    model = AssessmentAnswer
    extra = 0
    readonly_fields = ("score", "evaluated_at")


class AssessmentQuestionInline(admin.TabularInline):
    model = AssessmentQuestion
    extra = 0


@admin.register(UserAssessments)
class UserAssessmentsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "topic",
        "assessment_type",
        "difficulty",
        "status",
        "total_score",
        "max_score",
        "started_at",
    )
    list_filter = ("status", "difficulty", "assessment_type")
    search_fields = ("user__email", "topic__name")
    inlines = [AssessmentQuestionInline]


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "assessment", "question_type", "max_score")
    list_filter = ("question_type",)
    search_fields = ("question_text",)
    inlines = [AssessmentAnswerInline]


@admin.register(AssessmentAnswer)
class AssessmentAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "score", "evaluated_at")
    search_fields = ("user_answer",)