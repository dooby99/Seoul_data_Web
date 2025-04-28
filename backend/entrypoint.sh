#!/bin/bash

# 마이그레이션 수행
python manage.py makemigrations
python manage.py migrate

# 서버 실행
python manage.py runserver 0.0.0.0:8000
