from django.contrib import admin
from .models import Board

@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'created_at')
    search_fields = ('title', 'author_username')
    list_filter = ('created_at',)
