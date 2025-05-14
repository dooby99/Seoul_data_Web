# 베이스 이미지
FROM python:3.10-slim

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리 생성
WORKDIR /app

# 의존성 복사 및 설치
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# 프로젝트 파일 복사
COPY . /app/

# 권한 설정 및 엔트리포인트 실행
RUN chmod +x entrypoint.sh

CMD ["sh", "./entrypoint.sh"]