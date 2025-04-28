# pickon_kafka/config.py

import os
from dotenv import load_dotenv

# .env 파일 로딩
load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092').split(',')
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'user_log')
