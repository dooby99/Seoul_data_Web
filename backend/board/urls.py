from django.urls import path
from .views import BoardListCreateView, BoardRetrieveUpdateDestroyView

urlpatterns = [
    path('', BoardListCreateView.as_view(), name='board_list_create'),  # GET(목록) + POST(작성)
    path('<int:pk>/', BoardRetrieveUpdateDestroyView.as_view(), name='board_detail'),  # GET(조회), PUT/PATCH(수정), DELETE(삭제)
]
