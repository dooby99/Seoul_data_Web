from rest_framework import generics
from .models import Board
from .serializers import BoardSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly

class BoardListCreateView(generics.ListCreateAPIView):
    queryset = Board.objects.all().order_by('-created_at')
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class BoardRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
