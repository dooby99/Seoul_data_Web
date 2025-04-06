import pandas as pd
import requests
import time

# 기준 년도-분기 리스트 생성 (2019년 1분기부터 2025년 2분기까지)
years = range(2019, 2026)
quarters = range(1, 5)
stdr_yyqu_list = [f"{year}{q}" for year in years for q in quarters]
stdr_yyqu_list = [code for code in stdr_yyqu_list if code <= "20252"]

# API 키 및 기본 URL 설정
API_KEY = '******'  # 인증키를 입력하세요
BASE_URL = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarSelngQq"

all_results = []

# 분기별로 데이터 수집
for code in stdr_yyqu_list:
    start_index = 1
    batch_size = 1000
    total_count = None

    while True:
        url = f"{BASE_URL}/{start_index}/{start_index + batch_size - 1}/{code}"
        print(f"요청 중: {url}")
        try:
            res = requests.get(url)
            data = res.json()

            result_info = data.get("VwsmTrdarSelngQq", {}).get("RESULT", {})
            if result_info.get("CODE") != "INFO-000":
                print(f"오류 발생: {result_info.get('MESSAGE')}")
                break

            if total_count is None:
                total_count = data["VwsmTrdarSelngQq"]["list_total_count"]

            rows = data["VwsmTrdarSelngQq"].get("row", [])
            all_results.extend(rows)

            start_index += batch_size

            if start_index > total_count:
                break

        except Exception as e:
            print(f"{code} 요청 중 오류 발생: {e}")
            break

        time.sleep(1)

df.to_csv('서울시_직장인구_상권.csv', index=False)

#####################mapping########################
# 상권코드에 맞춘 자치구와 행정동 포함
SERVICE_NAME = 'TbgisTrdarRelm'
BASE_URL = f'http://openapi.seoul.go.kr:8088/{API_KEY}/json/{SERVICE_NAME}/'

def fetch_data(start, end):
    url = f'{BASE_URL}{start}/{end}/'
    response = requests.get(url)
    if response.status_code == 200:
        try:
            data = response.json()
            rows = data.get(SERVICE_NAME, {}).get('row', [])
            return rows
        except Exception as e:
            print(f'JSON 파싱 오류: {e}')
    else:
        print(f'요청 실패: {response.status_code}')
    return None

# 반복 수집
all_data = []
start = 1
batch_size = 1000

while True:
    end = start + batch_size - 1
    print(f"수집 중: {start} ~ {end}")
    rows = fetch_data(start, end)
    
    # 오류거나 빈 데이터일 경우 종료
    if not rows:
        print("더 이상 데이터가 없거나 오류 발생. 종료.")
        break

    all_data.extend(rows)
    start += batch_size
    time.sleep(0.2)  # API 과부하 방지

# DataFrame으로 변환
df = pd.DataFrame(all_data)
area_selected = df[['TRDAR_CD', 'SIGNGU_CD_NM', 'ADSTRD_CD_NM']].copy()

# 직장인구 상권 데이터
work_df = pd.read_csv("서울시_직장인구_상권.csv")  # 기존 파일저장이 필요없을시 앞선 파일을 csv생성하지 않고 df사용

# TRDAR_CD 형 일치 확인
area_selected['TRDAR_CD'] = area_selected['TRDAR_CD'].astype(str)
work_df['TRDAR_CD'] = work_df['TRDAR_CD'].astype(str)

merged_df = pd.merge(work_df, area_selected, on='TRDAR_CD', how='left')

# 컬럼명 한국어(필요없을시 주석처리 무관)
column_rename_dict = {
    'STDR_YYQU_CD': '기준년도분기',
    'TRDAR_SE_CD': '상권구분코드',
    'TRDAR_SE_CD_NM': '상권구분명',
    'TRDAR_CD': '상권코드',
    'TRDAR_CD_NM': '상권명',
    'TOT_WRC_POPLTN_CO': '총직장인구수',
    'ML_WRC_POPLTN_CO': '남성직장인구수',
    'FML_WRC_POPLTN_CO': '여성직장인구수',
    'AGRDE_10_WRC_POPLTN_CO': '10대직장인구수',
    'AGRDE_20_WRC_POPLTN_CO': '20대직장인구수',
    'AGRDE_30_WRC_POPLTN_CO': '30대직장인구수',
    'AGRDE_40_WRC_POPLTN_CO': '40대직장인구수',
    'AGRDE_50_WRC_POPLTN_CO': '50대직장인구수',
    'AGRDE_60_ABOVE_WRC_POPLTN_CO': '60대이상직장인구수',
    'MAG_10_WRC_POPLTN_CO': '남성10대직장인구수',
    'MAG_20_WRC_POPLTN_CO': '남성20대직장인구수',
    'MAG_30_WRC_POPLTN_CO': '남성30대직장인구수',
    'MAG_40_WRC_POPLTN_CO': '남성40대직장인구수',
    'MAG_50_WRC_POPLTN_CO': '남성50대직장인구수',
    'MAG_60_ABOVE_WRC_POPLTN_CO': '남성60대이상직장인구수',
    'FAG_10_WRC_POPLTN_CO': '여성10대직장인구수',
    'FAG_20_WRC_POPLTN_CO': '여성20대직장인구수',
    'FAG_30_WRC_POPLTN_CO': '여성30대직장인구수',
    'FAG_40_WRC_POPLTN_CO': '여성40대직장인구수',
    'FAG_50_WRC_POPLTN_CO': '여성50대직장인구수',
    'FAG_60_ABOVE_WRC_POPLTN_CO': '여성60대이상직장인구수',
    'SIGNGU_CD_NM': '자치구',
    'ADSTRD_CD_NM': '행정동'
}

merged_df.rename(columns=column_rename_dict, inplace=True)

# 결과 확인
# merged_df
merged_df.to_csv('서울시_직장인구_상권_위치포함.csv', index=False)
