from rest_framework import serializers
from .models import Board

class BoardSerializer(serializers.ModelSerializer):
    author_id = serializers.ReadOnlyField(source='author.id')
    author_username = serializers.ReadOnlyField(source='author.username')
    author_nickname = serializers.ReadOnlyField(source='author.first_name')
    class Meta:
        model = Board
        fields = ['id', 'title', 'content', 'author_id', 'author_username', 'author_nickname', 'created_at', 'updated_at']
