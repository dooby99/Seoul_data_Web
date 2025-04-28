# pickon_kafka/consumer.py

import time
import json
import redis
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from pickon_kafka.config import KAFKA_BOOTSTRAP_SERVERS, REDIS_HOST, REDIS_PORT

MAX_RETRIES = 10
WAIT_SECONDS = 5

# Kafka 연결 재시도
for i in range(MAX_RETRIES):
    try:
        consumer = KafkaConsumer(
            'user_log',
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id='user_log_consumer_group',   # ✅ 추가!!
            auto_offset_reset='latest',
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            # consumer_timeout_ms=10000
        )
        print("✅ Kafka 연결 성공")
        break
    except NoBrokersAvailable:
        print(f"❌ Kafka 연결 실패... 재시도 {i+1}/{MAX_RETRIES}")
        time.sleep(WAIT_SECONDS)
else:
    raise Exception("Kafka에 연결할 수 없습니다.")

# Redis 연결
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

def aggregate_log():
    print("📥 Kafka Consumer listening...")
    while True:
        try:
            for msg in consumer:
                data = msg.value
                print("🔥 Logged:", data)

                gu = data.get("gu")
                dong = data.get("dong")
                category = data.get("category")
                area_type = data.get("area_type")
                gender = data.get("gender")
                age = data.get("age")

                if gu:
                    r.zincrby("hot:gu", 1, gu)
                if dong:
                    r.zincrby("hot:dong", 1, dong)
                if category:
                    r.zincrby("hot:category", 1, category)
                if area_type:
                    r.zincrby("hot:area_type", 1, area_type)
                if gender:
                    r.zincrby("hot:gender", 1, gender)
                if age:
                    r.zincrby("hot:age", 1, age)

                print("🔥 Logged:", data)
        except Exception as e:
            print(f"❗ Error in consumer: {e}")
        finally:
            consumer.close()

if __name__ == "__main__":
    aggregate_log()