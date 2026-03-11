from django.urls import path
from learn.views.learning_category_views import ListLearningCategories
from learn.views.learning_topic_views import ListLearningTopics, TopicDetailView
from learn.views.learn_views import (
    GenerateQuestion, AnswerResults, ListUserLearningHistory
)
from learn.views.learning_notes_views import (
    ListLearningNotes, CreateLearningNote, UpdateLearningNote, DeleteLearningNote
)

# base url - /learn/

urlpatterns = [
    path('categories/list', ListLearningCategories.as_view()),
    path('topics/list', ListLearningTopics.as_view()),
    path('topic/<int:topic_id>/details', TopicDetailView.as_view()),
    
    path('generate/<uuid:topic_id>/question', GenerateQuestion.as_view()),
    path('question/answer/result', AnswerResults.as_view()),
    path('topic/<int:topic_id>/history', ListUserLearningHistory.as_view()),
    
    
    # learn notes 
    path("notes/list", ListLearningNotes.as_view()),
    path("notes/create", CreateLearningNote.as_view()),
    path("notes/<int:note_id>/update", UpdateLearningNote.as_view()),
    path("notes/<int:note_id>/delete", DeleteLearningNote.as_view()),
]
