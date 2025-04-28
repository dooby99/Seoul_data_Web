from django.urls import path
from .views import recommend_view, get_hot_topics

urlpatterns = [
    path('recommend/', recommend_view, name='recommend_api'),
    path('hot_topics/', get_hot_topics),

]
