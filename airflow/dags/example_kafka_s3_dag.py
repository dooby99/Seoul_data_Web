# airflow/dags/redis_hot_topics_to_s3.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import redis
import json
import boto3
import os

# 기본 DAG 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# S3 설정
AWS_REGION = 'ap-northeast-2'
S3_BUCKET = 'seouldata'

# Redis 설정
REDIS_HOST = 'redis'
REDIS_PORT = 6379

def export_redis_to_s3():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    
    hot_keys = ["hot:gu", "hot:dong", "hot:category", "hot:gender", "hot:age"]
    data = {}

    for key in hot_keys:
        entries = r.zrevrange(key, 0, -1, withscores=True)
        data[key] = [
            {"name": item[0].decode('utf-8'), "count": int(item[1])}
            for item in entries
        ]
    
    # S3 경로: hot_topics/{year}/{month}/{day}/hot_topics_{date}.json
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    date_str = now.strftime("%Y%m%d")
    
    s3_key = f"hot_topics/{year}/{month}/{day}/hot_topics_{date_str}.json"

    s3 = boto3.client('s3', region_name=AWS_REGION)
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=json.dumps(data, ensure_ascii=False),
        ContentType='application/json'
    )
    print(f"✅ S3 저장 완료: {s3_key}")

def clear_redis_hot_topics():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    hot_keys = ["hot:gu", "hot:dong", "hot:category", "hot:gender", "hot:age"]
    
    for key in hot_keys:
        r.delete(key)
    print("🧹 Redis 핫토픽 초기화 완료")

# DAG 정의
with DAG(
    dag_id='redis_to_s3_and_reset_hot_topics',
    default_args=default_args,
    start_date=datetime(2025, 4, 18),
    schedule_interval='0 0 * * *',  # 매일 00:00
    catchup=False,
    tags=['hot_topics', 'redis', 's3'],
) as dag:
    
    export_task = PythonOperator(
        task_id='export_redis_to_s3',
        python_callable=export_redis_to_s3
    )

    clear_task = PythonOperator(
        task_id='clear_redis_keys',
        python_callable=clear_redis_hot_topics
    )

    export_task >> clear_task
