# recommend/views.py
import json
import redis
from django.http import JsonResponse
from .utils import recommend, generate_report_from_input
from django.views.decorators.csrf import csrf_exempt
from pickon_kafka.producer import send_log_to_kafka
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Redis 연결
r = redis.Redis(host='redis', port=6379, db=0)


@api_view(['GET'])
def get_hot_topics(request):
    result = {
        "hot_gu": [],
        "hot_dong": [],
        "hot_category": [],
        "hot_gender": [],
        "hot_age": []
    }
    
    # Redis에서 상위 5개 가져오기
    try:
        for key in result.keys():
            data = r.zrevrange(key.replace("hot_", "hot:"), 0, 4, withscores=True)
            result[key] = [{"name": item[0].decode('utf-8'), "count": int(item[1])} for item in data]
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=500)

    return Response({"status": "success", "data": result})


@api_view(['POST'])
def recommend_view(request):
    try:
        body = request.data

        # 추천 시스템용으로 변환
        user_input = {
            "자치구_코드_명": body.get("gu"),
            "행정동_코드_명": body.get("dong"),
            "상권_구분_코드_명": body.get("area_type"),
            "서비스_업종_코드_명": body.get("category"),
            "성별": body.get("gender"),
            "연령대": body.get("age"),
        }
        send_log_to_kafka(user_input)

        result = recommend(user_input)
        report = generate_report_from_input(user_input)


        return Response({"status": "success", "data": result, "report": report})

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Only POST method allowed"})
 