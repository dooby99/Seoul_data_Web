# pickon_kafka/producer.py
from kafka import KafkaProducer
import json
from datetime import datetime

# 초기화 지연
producer = None

def get_producer():
    global producer
    if producer is None:
        producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
        )
    return producer

def send_log_to_kafka(user_input):
    try:
        data = {
            "gu": user_input["자치구_코드_명"],
            "dong": user_input["행정동_코드_명"],
            "area_type": user_input["상권_구분_코드_명"],
            "category": user_input["서비스_업종_코드_명"],
            "gender": user_input["성별"],
            "age": user_input["연령대"],
            "timestamp": datetime.now().isoformat()
        }
        producer = get_producer()  # ✅ producer를 한번만 호출
        producer.send('user_log', value=data)
        producer.flush()
    except Exception as e:
        print(f"❗ Error sending log to Kafka: {e}")