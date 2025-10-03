from django.contrib import admin
from learn.models import AIModels, LearningCategory, LearningTopic, UserLearningHistory
# Register your models here.


admin.site.register(AIModels)
admin.site.register(LearningCategory)
admin.site.register(LearningTopic)
admin.site.register(UserLearningHistory)