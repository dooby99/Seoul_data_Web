#recommend/models.py
from django.db import models

class RecommendationLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    gu = models.CharField(max_length=50)
    dong = models.CharField(max_length=50, blank=True, null=True)
    area_type = models.CharField(max_length=50)
    category = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, blank=True, null=True)
    age = models.CharField(max_length=10, blank=True, null=True)
    success_prob = models.FloatField()
    status = models.CharField(max_length=20)  # 예: '추천' / '비추천'

    def __str__(self):
        return f"[{self.timestamp}] {self.gu} {self.dong or ''} {self.category} → {self.success_prob:.2f}"
