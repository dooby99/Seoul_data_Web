import pandas as pd
import requests
import time

# 기준 년도-분기 리스트 생성 (2019년 1분기부터 2025년 2분기까지)
years = range(2019, 2026)
quarters = range(1, 5)
stdr_yyqu_list = [f"{year}{q}" for year in years for q in quarters]
stdr_yyqu_list = [code for code in stdr_yyqu_list if code <= "20252"]

# API 키 및 기본 URL 설정
API_KEY = '*******'
BASE_URL = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/VwsmTrdarSelngQq"

# 전체 결과 저장용 dict
df_by_quarter = {}

for code in stdr_yyqu_list:
    print(f"📦 {code} 데이터 수집 중...")
    start_index = 1
    batch_size = 1000
    total_count = None
    results = []

    while True:
        url = f"{BASE_URL}/{start_index}/{start_index + batch_size - 1}/{code}"
        try:
            response = requests.get(url)
            data = response.json()

            result_info = data.get("VwsmTrdarSelngQq", {}).get("RESULT", {})
            if result_info.get("CODE") != "INFO-000":
                print(f"오류 발생: {result_info.get('MESSAGE')}")
                break

            if total_count is None:
                total_count = data["VwsmTrdarSelngQq"]["list_total_count"]

            rows = data["VwsmTrdarSelngQq"].get("row", [])
            if not rows:
                print(f"{code}는 수집된 데이터가 없습니다.")
                break

            results.extend(rows)
            start_index += batch_size

            if start_index > total_count:
                break

        except Exception as e:
            print(f"{code} 요청 중 오류 발생: {e}")
            break

        time.sleep(1)  # 과도한 요청 방지

    # 분기별 데이터프레임으로 저장
    if results:
        df_quarter = pd.DataFrame(results)
        df_by_quarter[code] = df_quarter

        # CSV 파일로 저장 (원할 경우 주석 해제)
        df_quarter.to_csv(f"서울시_추정매출_상권.csv", index=False)


############# 컬럼명 한글화 + 자치구 행정동 #################

area_selected = df[['TRDAR_CD', 'SIGNGU_CD_NM', 'ADSTRD_CD_NM']].copy()

# 직장인구 상권 데이터 예시
work_df = pd.read_csv("서울시_추정매출_상권.csv")  # df_quarter 사용 무관

# TRDAR_CD가 정수형일 수 있으므로 형 일치 확인
area_selected['TRDAR_CD'] = area_selected['TRDAR_CD'].astype(str)
work_df['TRDAR_CD'] = work_df['TRDAR_CD'].astype(str)

# 병합
merged_df = pd.merge(work_df, area_selected, on='TRDAR_CD', how='left')

sales_column_rename_dict = {
    'STDR_YYQU_CD': '기준년분기코드',
    'TRDAR_SE_CD': '상권구분코드',
    'TRDAR_SE_CD_NM': '상권구분명',
    'TRDAR_CD': '상권코드',
    'TRDAR_CD_NM': '상권명',
    'SVC_INDUTY_CD': '서비스업종코드',
    'SVC_INDUTY_CD_NM': '서비스업종명',

    'THSMON_SELNG_AMT': '당월매출금액',
    'THSMON_SELNG_CO': '당월매출건수',
    'MDWK_SELNG_AMT': '주중매출금액',
    'WKEND_SELNG_AMT': '주말매출금액',

    'MON_SELNG_AMT': '월요일매출금액',
    'TUES_SELNG_AMT': '화요일매출금액',
    'WED_SELNG_AMT': '수요일매출금액',
    'THUR_SELNG_AMT': '목요일매출금액',
    'FRI_SELNG_AMT': '금요일매출금액',
    'SAT_SELNG_AMT': '토요일매출금액',
    'SUN_SELNG_AMT': '일요일매출금액',

    'TMZON_00_06_SELNG_AMT': '시간대00_06매출금액',
    'TMZON_06_11_SELNG_AMT': '시간대06_11매출금액',
    'TMZON_11_14_SELNG_AMT': '시간대11_14매출금액',
    'TMZON_14_17_SELNG_AMT': '시간대14_17매출금액',
    'TMZON_17_21_SELNG_AMT': '시간대17_21매출금액',
    'TMZON_21_24_SELNG_AMT': '시간대21_24매출금액',

    'ML_SELNG_AMT': '남성매출금액',
    'FML_SELNG_AMT': '여성매출금액',

    'AGRDE_10_SELNG_AMT': '연령대10매출금액',
    'AGRDE_20_SELNG_AMT': '연령대20매출금액',
    'AGRDE_30_SELNG_AMT': '연령대30매출금액',
    'AGRDE_40_SELNG_AMT': '연령대40매출금액',
    'AGRDE_50_SELNG_AMT': '연령대50매출금액',
    'AGRDE_60_ABOVE_SELNG_AMT': '연령대60이상매출금액',

    'MDWK_SELNG_CO': '주중매출건수',
    'WKEND_SELNG_CO': '주말매출건수',

    'MON_SELNG_CO': '월요일매출건수',
    'TUES_SELNG_CO': '화요일매출건수',
    'WED_SELNG_CO': '수요일매출건수',
    'THUR_SELNG_CO': '목요일매출건수',
    'FRI_SELNG_CO': '금요일매출건수',
    'SAT_SELNG_CO': '토요일매출건수',
    'SUN_SELNG_CO': '일요일매출건수',

    'TMZON_00_06_SELNG_CO': '시간대00_06매출건수',
    'TMZON_06_11_SELNG_CO': '시간대06_11매출건수',
    'TMZON_11_14_SELNG_CO': '시간대11_14매출건수',
    'TMZON_14_17_SELNG_CO': '시간대14_17매출건수',
    'TMZON_17_21_SELNG_CO': '시간대17_21매출건수',
    'TMZON_21_24_SELNG_CO': '시간대21_24매출건수',

    'ML_SELNG_CO': '남성매출건수',
    'FML_SELNG_CO': '여성매출건수',

    'AGRDE_10_SELNG_CO': '연령대10매출건수',
    'AGRDE_20_SELNG_CO': '연령대20매출건수',
    'AGRDE_30_SELNG_CO': '연령대30매출건수',
    'AGRDE_40_SELNG_CO': '연령대40매출건수',
    'AGRDE_50_SELNG_CO': '연령대50매출건수',
    'AGRDE_60_ABOVE_SELNG_CO': '연령대60이상매출건수',

    'SIGNGU_CD_NM': '자치구',
    'ADSTRD_CD_NM': '행정동'
}
merged_df.rename(columns=sales_column_rename_dict, inplace=True)

merged_df.to_csv('서울시_추정매출_상권_위치포함.csv', index=False)
