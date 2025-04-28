# # backend/recommend/utils.py

import os
import pandas as pd
import boto3
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder


IS_DEV = os.environ.get('DJANGO_DEVELOPMENT', 'False') == 'True'

# S3에서 파일 다운로드 함수
def download_from_s3(bucket_name, s3_key, local_path):
    if IS_DEV:
        print("[임시] 개발환경: S3 다운로드 스킵")
        return
    s3 = boto3.client('s3', region_name='ap-northeast-2')
    if not os.path.exists(os.path.dirname(local_path)):
        os.makedirs(os.path.dirname(local_path))
    s3.download_file(bucket_name, s3_key, local_path)

# 전역 변수
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bucket_name = "seouldata"

# 1) 모델 다운로드
model = XGBClassifier()
model_local_path = os.path.join(BASE_DIR, "models", "xgb_best_model.json")
model_key = "backend/models/xgb_best_model.json"

if not os.path.exists(model_local_path):
    download_from_s3(bucket_name, model_key, model_local_path)


if IS_DEV:
    print("[임시] 개발환경: 모델 로드 스킵")
else:
    model.load_model(model_local_path)

# 2) ppl_avg.csv 다운로드
ppl_local_path = os.path.join(BASE_DIR, "data", "ppl_avg.csv")
ppl_key = "backend/data/ppl_avg.csv"

if not os.path.exists(ppl_local_path):
    download_from_s3(bucket_name, ppl_key, ppl_local_path)

# 3) store_avg.csv 다운로드
store_local_path = os.path.join(BASE_DIR, "data", "store_avg.csv")
store_key = "backend/data/store_avg.csv"

if not os.path.exists(store_local_path):
    download_from_s3(bucket_name, store_key, store_local_path)

# 4) 통합상권 데이터 다운로드
total_data_path = os.path.join(BASE_DIR, "data", "통합 상권 데이터.csv") 
total_key = "backend/data/통합 상권 데이터.csv"

if not os.path.exists(total_data_path):
    download_from_s3(bucket_name, total_key, total_data_path)

# 4) CSV 불러오기
if IS_DEV:
    print("[임시] 개발환경: CSV 로드 스킵 (빈 데이터프레임 생성)")
    ppl_df = pd.DataFrame()
    store_df = pd.DataFrame()
    all_df = pd.DataFrame()
else:
    ppl_df = pd.read_csv(ppl_local_path)
    store_df = pd.read_csv(store_local_path)
    all_df = pd.read_csv(total_data_path)
    all_df.columns = all_df.columns.str.strip()

# 리포트 함수들
# 가장 매출이 높은 상권을 대표 상권으로 간주
def get_representative_area_name(df, dong_name):
    subset = df[df["행정동_코드_명"] == dong_name]
    if subset.empty:
        return None
    return subset.sort_values(by="당월_매출_금액", ascending=False).iloc[0]["상권_코드_명"]

def generate_report(area_name, sector_name, user_input):
    df = all_df
    print("[리포트 생성 시도] area_name:", area_name, "| sector_name:", sector_name)

    # 사용자 입력 기준 필터
    gu_name = user_input.get("자치구_코드_명", "")
    dong_name = user_input.get("행정동_코드_명", "")
    if not gu_name or not dong_name:
        return "자치구 및 행정동 정보가 필요합니다."

    # 비교 대상: 자치구, 행정동, 업종 모두 일치
    filtered_df = df[
        (df["자치구_코드_명"] == gu_name) &
        (df["행정동_코드_명"] == dong_name) &
        (df["서비스_업종_코드_명"] == sector_name)
    ]

    if filtered_df.empty:
        return "해당 조건에 맞는 비교 데이터가 없습니다."

    sel = filtered_df[filtered_df["상권_코드_명"] == area_name]
    if sel.empty:
        return "해당 상권에 대한 리포트를 생성할 수 없습니다."
    row = sel.iloc[0]

    age_group = user_input.get("연령대", "").replace("대", "")
    gender = user_input.get("성별", "")
    age_col = f"연령대_{age_group}_유동인구_수"
    age_pop = row.get(age_col, 0) if age_group else 0
    total_pop = row.get("총_유동인구_수", 1)
    age_ratio = (age_pop / total_pop) * 100 if total_pop else 0

    # 월 평균 매출
    annual_sales = row.get("당월_매출_금액", 0)
    print("당월 매출 금액 : ", annual_sales)
    monthly_sales = int(annual_sales / 12) if annual_sales else 0
    print("매출 금액 / 12", monthly_sales)

    # 비교 대상: 동일 구 + 동 + 업종
    percentile = (filtered_df["당월_매출_금액"] < annual_sales).sum() / len(filtered_df) * 100 if not filtered_df.empty else 0

    if percentile >= 90:
        평가문장 = "해당 업종은 이 지역에서 매우 활발하게 운영되고 있는 것으로 보입니다."
    elif percentile >= 65:
        평가문장 = "해당 업종은 이 지역에서 평균 이상의 성과를 보이고 있습니다."
    elif percentile >= 40:
        평가문장 = "해당 업종은 이 지역에서 평균 이하의 성과를 보이고 있습니다."
    else:
        평가문장 = "해당 업종은 이 지역에서 다소 저조하게 운영되고 있는 것으로 보입니다."

    report = f"[상권명: {area_name}] [업종: {sector_name}]"

    if not pd.isna(row.get("점포_수")):
        report += f"\n총 점포 수: {int(row['점포_수'])}개"

    if not pd.isna(row.get("폐업_률")) and row["폐업_률"] > 0:
        report += f", 폐업률: {row['폐업_률']:.1f}%"

    if not pd.isna(monthly_sales):
        report += f", 평균 월매출: {monthly_sales:,}원"

    # 유사 업종 점포 수 (같은 동+구+업종 내 합계)
    similar_sector_count = filtered_df["점포_수"].sum() if "점포_수" in filtered_df.columns else None
    if similar_sector_count:
        report += f"\n동일 지역 내 유사 업종 총 점포 수: {int(similar_sector_count):,}개"

    if age_group and gender:
        report += f"\n{age_group}대 {gender} 유동 인구: {int(age_pop):,}명/일, 전체 중 {age_ratio:.1f}%"

    if not pd.isna(row.get("총_직장_인구_수")):
        report += f"\n직장인 수: {int(row['총_직장_인구_수']):,}명"

    report += f"\n{평가문장}"
    return report.strip()


# def generate_report(area_name, sector_name, user_input):
#     df = all_df
#     print("[리포트 생성 시도] area_name:", area_name, "| sector_name:", sector_name)

#     sel = df[(df["상권_코드_명"] == area_name) & (df["서비스_업종_코드_명"] == sector_name)]
#     if sel.empty:
#         print("[리포트 실패] 상권 또는 업종 조건에 맞는 데이터가 없음")
#         return "해당 상권에 대한 리포트를 생성할 수 없습니다."
#     row = sel.iloc[0]

#     age_group = user_input.get("연령대", "").replace("대", "")
#     gender = user_input.get("성별", "")

#     age_col = f"연령대_{age_group}_유동인구_수"
#     age_pop = row.get(age_col, 0) if age_group else 0
#     total_pop = row.get("총_유동인구_수", 1)
#     age_ratio = (age_pop / total_pop) * 100 if total_pop else 0

#     sales_value = row.get("당월_매출_금액", 0)
#     all_sector = df[df["서비스_업종_코드_명"] == sector_name]
#     percentile = (all_sector["당월_매출_금액"] < sales_value).sum() / len(all_sector) * 100 if not all_sector.empty else 0

#     if percentile >= 90:
#         평가문장 = "해당 업종은 이 지역에서 매우 활발하게 운영되고 있는 것으로 보입니다."
#     elif percentile >= 70:
#         평가문장 = "해당 업종은 이 지역에서 평균 이상의 성과를 보이고 있습니다."
#     elif percentile >= 50:
#         평가문장 = "해당 업종은 이 지역에서 평균 이하의 성과를 보이고 있습니다."
#     else:
#         평가문장 = "해당 업종은 이 지역에서 다소 저조하게 운영되고 있는 것으로 보입니다."

#     report = f"[상권명: {area_name}] [업종: {sector_name}]"

#     if not pd.isna(row.get("점포_수")) and not pd.isna(row.get("폐업_률")) and not pd.isna(row.get("당월_매출_금액")):
#         report += f"\n총 점포 수: {int(row['점포_수'])}개, 폐업률: {row['폐업_률']:.1f}%, 평균 월매출: {int(row['당월_매출_금액']):,}원"

#     if age_group and gender:
#         report += f"\n{age_group}대 {gender} 유동 인구: {int(age_pop):,}명/일, 전체 유동 인구 중 비중: {age_ratio:.1f}%"

#     if not pd.isna(row.get("총_직장_인구_수")):
#         report += f"\n직장인 수: {int(row['총_직장_인구_수']):,}명"

#     report += f"\n{평가문장}"
#     return report.strip()

def generate_report_from_input(user_input):
    dong = user_input.get("행정동_코드_명", "")
    sector = user_input.get("서비스_업종_코드_명", "")
    if not dong or not sector:
        return "입력값 부족으로 리포트를 생성할 수 없습니다."
    area_code = get_representative_area_name(all_df, dong)
    if not area_code:
        return "상권 정보 없음"
    return generate_report(area_code, sector, user_input)


def clean_user_input(user_input):
    return {
        "자치구_코드_명": user_input["자치구_코드_명"],
        "행정동_코드_명": user_input.get("행정동_코드_명") or "",
        "상권_구분_코드_명": user_input["상권_구분_코드_명"],
        "서비스_업종_코드_명": user_input["서비스_업종_코드_명"],
        "성별": user_input.get("성별") or None,
        "연령대": user_input.get("연령대") or None
    }

# 유동인구에 성별/연령별 가중치 반영
def apply_weight(row, gender=None, age=None):
    scale = 1

    if pd.isna(row["총_유동인구_수"]) or row["총_유동인구_수"] == 0:
        return row

    if gender in ["남성", "여성"]:
        column = f"{gender}_유동인구_수"
        if not pd.isna(row.get(column)):
            scale *= row[column] / row["총_유동인구_수"]

    if age:
        age_column = None
        if age == "20대":
            age_column = "연령대_20_유동인구_수"
        elif age == "30대":
            age_column = "연령대_30_유동인구_수"
        elif age == "40대":
            age_column = "연령대_40_유동인구_수"
        elif age == "50대":
            age_column = "연령대_50_유동인구_수"

        if age_column and not pd.isna(row.get(age_column)):
            scale *= row[age_column] / row["총_유동인구_수"]

    row["총_유동인구_수"] *= scale
    row["남성_유동인구_수"] *= scale
    row["여성_유동인구_수"] *= scale

    return row

# 범주형 컬럼 인코딩
def encode(df):
    for col in ["자치구_코드_명", "행정동_코드_명", "상권_구분_코드_명", "서비스_업종_코드_명"]:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
    return df

# 추천 함수
def recommend(user_input):
    try:
        user_input = clean_user_input(user_input)
        report_text = generate_report_from_input(user_input)

        gu = user_input["자치구_코드_명"]
        dong = user_input["행정동_코드_명"]
        area_type = user_input["상권_구분_코드_명"]
        category = user_input["서비스_업종_코드_명"]
        gender = user_input["성별"]
        age = user_input["연령대"]

        cols = [
            "총_유동인구_수", "남성_유동인구_수", "여성_유동인구_수",
            "연령대_20_유동인구_수", "연령대_30_유동인구_수",
            "연령대_40_유동인구_수", "연령대_50_유동인구_수",
            "점포_수", "유사_업종_점포_수", "프랜차이즈_점포_수",
            "개업_율", "폐업_률", "총_직장_인구_수",
            "자치구_코드_명", "행정동_코드_명", "상권_구분_코드_명", "서비스_업종_코드_명",
            "X좌표", "Y좌표"
        ]

        # ppl_row 조회
        ppl_row = ppl_df.query("자치구_코드_명 == @gu and 행정동_코드_명 == @dong") if dong \
            else ppl_df.query("자치구_코드_명 == @gu").groupby("자치구_코드_명").mean(numeric_only=True).reset_index()

        if ppl_row.empty:
            return {"status": "error", "message": "해당 자치구/행정동에 대한 유동인구 데이터가 없습니다."}

        ppl_row = ppl_row.fillna(0)
        if not dong:
            ppl_row["행정동_코드_명"] = ""

        # store_row 조회
        store_row_query = store_df.query("자치구_코드_명 == @gu and 서비스_업종_코드_명 == @category")
        if store_row_query.empty:
            return {"status": "error", "message": "해당 자치구/업종에 대한 상점 데이터가 없습니다."}

        store_row = store_row_query.iloc[0]

        # ------------- 현재 조건 추천 (Single Recommend) -------------
        base_input = ppl_row.copy()
        base_input = base_input.apply(lambda row: apply_weight(row, gender, age), axis=1)

        # 상점 정보 덮어쓰기 (명시적 매핑)
        base_input["점포_수"] = store_row["점포_수"]
        base_input["유사_업종_점포_수"] = store_row["유사_업종_점포_수"]
        base_input["프랜차이즈_점포_수"] = store_row["프랜차이즈_점포_수"]
        base_input["개업_율"] = store_row["가중_개업_률"]
        base_input["폐업_률"] = store_row["가중_폐업_률"]
        base_input["상권_구분_코드_명"] = area_type
        base_input["서비스_업종_코드_명"] = category

        df_main = encode(base_input[cols].copy())
        success_prob = model.predict_proba(df_main)[0][1]
        single_result = {
            "success_prob": round(float(success_prob), 4),
            "recommendation": "추천" if success_prob >= 0.85 else "비추천"
        }

        # ------------- 행정동 추천 (Top5 Dong Recommend) -------------
        dong_df = ppl_df.query("자치구_코드_명 == @gu").copy()
        dong_df = dong_df.fillna(0)
        dong_df = dong_df.apply(lambda row: apply_weight(row, gender, age), axis=1)

        dong_df["점포_수"] = store_row["점포_수"]
        dong_df["유사_업종_점포_수"] = store_row["유사_업종_점포_수"]
        dong_df["프랜차이즈_점포_수"] = store_row["프랜차이즈_점포_수"]
        dong_df["개업_율"] = store_row["가중_개업_률"]
        dong_df["폐업_률"] = store_row["가중_폐업_률"]
        dong_df["상권_구분_코드_명"] = area_type
        dong_df["서비스_업종_코드_명"] = category

        dong_preds = encode(dong_df[cols].copy())
        dong_df["성공확률"] = model.predict_proba(dong_preds)[:, 1]
        dong_df["성공확률"] = dong_df["성공확률"].apply(lambda x: round(float(x), 4))

        dong_recommend = dong_df[["행정동_코드_명", "성공확률"]] \
            .sort_values(by="성공확률", ascending=False).head(5).to_dict(orient="records")

        # ------------- 업종 추천 (Top5 Category Recommend) -------------
        ppl_base = ppl_df.query("자치구_코드_명 == @gu")
        if dong:
            ppl_base = ppl_base.query("행정동_코드_명 == @dong")

        if ppl_base.empty:
            return {"status": "error", "message": "해당 조건에 맞는 유동인구 데이터가 없습니다."}

        ppl_base = ppl_base.iloc[0]
        ppl_base = apply_weight(ppl_base, gender, age)

        업종추천 = store_df.query("자치구_코드_명 == @gu").copy()

        result_list = []
        for _, row in 업종추천.iterrows():
            row_data = {
                "총_유동인구_수": ppl_base["총_유동인구_수"],
                "남성_유동인구_수": ppl_base["남성_유동인구_수"],
                "여성_유동인구_수": ppl_base["여성_유동인구_수"],
                "연령대_20_유동인구_수": ppl_base["연령대_20_유동인구_수"],
                "연령대_30_유동인구_수": ppl_base["연령대_30_유동인구_수"],
                "연령대_40_유동인구_수": ppl_base["연령대_40_유동인구_수"],
                "연령대_50_유동인구_수": ppl_base["연령대_50_유동인구_수"],
                "점포_수": row["점포_수"],
                "유사_업종_점포_수": row["유사_업종_점포_수"],
                "프랜차이즈_점포_수": row["프랜차이즈_점포_수"],
                "개업_율": row["가중_개업_률"],
                "폐업_률": row["가중_폐업_률"],
                "총_직장_인구_수": ppl_base["총_직장_인구_수"],
                "자치구_코드_명": gu,
                "행정동_코드_명": dong,
                "상권_구분_코드_명": area_type,
                "서비스_업종_코드_명": row["서비스_업종_코드_명"],
                "X좌표": ppl_base["X좌표"],
                "Y좌표": ppl_base["Y좌표"]
            }
            result_list.append(row_data)

        업종_df = pd.DataFrame(result_list)
        업종_preds = encode(업종_df[cols].copy())
        업종_df["성공확률"] = model.predict_proba(업종_preds)[:, 1]
        업종_df["성공확률"] = 업종_df["성공확률"].apply(lambda x: round(float(x), 4))

        category_recommend = 업종_df[["서비스_업종_코드_명", "성공확률"]] \
            .sort_values(by="성공확률", ascending=False).head(5).to_dict(orient="records")

        return {
            "현재조건": single_result,
            "행정동추천": dong_recommend,
            "업종추천": category_recommend,
            # "상권리포트": report_text
        }
    except Exception as e:
        import traceback
        traceback.print_exc()  # <- 콘솔에 전체 에러 출력
        return {"status": "error", "message": str(e)}

# ####################################
# # # backend/recommend/utils.py

# import os
# import pandas as pd
# import boto3
# from xgboost import XGBClassifier
# from sklearn.preprocessing import LabelEncoder

# # S3에서 파일 다운로드 함수
# def download_from_s3(bucket_name, s3_key, local_path):
#     s3 = boto3.client('s3', region_name='ap-northeast-2')
#     if not os.path.exists(os.path.dirname(local_path)):
#         os.makedirs(os.path.dirname(local_path))
#     s3.download_file(bucket_name, s3_key, local_path)

# # 전역 변수
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# bucket_name = "seouldata"

# # 1) 모델 다운로드
# model = XGBClassifier()
# model_local_path = os.path.join(BASE_DIR, "models", "xgb_best_model.json")
# model_key = "backend/models/xgb_best_model.json"

# if not os.path.exists(model_local_path):
#     download_from_s3(bucket_name, model_key, model_local_path)

# model.load_model(model_local_path)

# # 2) ppl_avg.csv 다운로드
# ppl_local_path = os.path.join(BASE_DIR, "data", "ppl_avg.csv")
# ppl_key = "backend/data/ppl_avg.csv"

# if not os.path.exists(ppl_local_path):
#     download_from_s3(bucket_name, ppl_key, ppl_local_path)

# # 3) store_avg.csv 다운로드
# store_local_path = os.path.join(BASE_DIR, "data", "store_avg.csv")
# store_key = "backend/data/store_avg.csv"

# if not os.path.exists(store_local_path):
#     download_from_s3(bucket_name, store_key, store_local_path)

# # 4) CSV 불러오기
# ppl_df = pd.read_csv(ppl_local_path)
# store_df = pd.read_csv(store_local_path)

# def clean_user_input(user_input):
#     return {
#         "자치구_코드_명": user_input["자치구_코드_명"],
#         "행정동_코드_명": user_input.get("행정동_코드_명") or "",
#         "상권_구분_코드_명": user_input["상권_구분_코드_명"],
#         "서비스_업종_코드_명": user_input["서비스_업종_코드_명"],
#         "성별": user_input.get("성별") or None,
#         "연령대": user_input.get("연령대") or None
#     }

# # 유동인구에 성별/연령별 가중치 반영
# def apply_weight(row, gender=None, age=None):
#     scale = 1

#     if pd.isna(row["총_유동인구_수"]) or row["총_유동인구_수"] == 0:
#         return row

#     if gender in ["남성", "여성"]:
#         column = f"{gender}_유동인구_수"
#         if not pd.isna(row.get(column)):
#             scale *= row[column] / row["총_유동인구_수"]

#     if age:
#         age_column = None
#         if age == "20대":
#             age_column = "연령대_20_유동인구_수"
#         elif age == "30대":
#             age_column = "연령대_30_유동인구_수"
#         elif age == "40대":
#             age_column = "연령대_40_유동인구_수"
#         elif age == "50대":
#             age_column = "연령대_50_유동인구_수"

#         if age_column and not pd.isna(row.get(age_column)):
#             scale *= row[age_column] / row["총_유동인구_수"]

#     row["총_유동인구_수"] *= scale
#     row["남성_유동인구_수"] *= scale
#     row["여성_유동인구_수"] *= scale

#     return row

# # 범주형 컬럼 인코딩
# def encode(df):
#     for col in ["자치구_코드_명", "행정동_코드_명", "상권_구분_코드_명", "서비스_업종_코드_명"]:
#         le = LabelEncoder()
#         df[col] = le.fit_transform(df[col].astype(str))
#     return df

# # 추천 함수
# def recommend(user_input):
#     user_input = clean_user_input(user_input)

#     gu = user_input["자치구_코드_명"]
#     dong = user_input["행정동_코드_명"]
#     area_type = user_input["상권_구분_코드_명"]
#     category = user_input["서비스_업종_코드_명"]
#     gender = user_input["성별"]
#     age = user_input["연령대"]

#     cols = [
#         "총_유동인구_수", "남성_유동인구_수", "여성_유동인구_수",
#         "연령대_20_유동인구_수", "연령대_30_유동인구_수",
#         "연령대_40_유동인구_수", "연령대_50_유동인구_수",
#         "점포_수", "유사_업종_점포_수", "프랜차이즈_점포_수",
#         "개업_율", "폐업_률", "총_직장_인구_수",
#         "자치구_코드_명", "행정동_코드_명", "상권_구분_코드_명", "서비스_업종_코드_명",
#         "X좌표", "Y좌표"
#     ]

#     # ppl_row 조회
#     ppl_row = ppl_df.query("자치구_코드_명 == @gu and 행정동_코드_명 == @dong") if dong \
#         else ppl_df.query("자치구_코드_명 == @gu").groupby("자치구_코드_명").mean(numeric_only=True).reset_index()

#     if ppl_row.empty:
#         return {"status": "error", "message": "해당 자치구/행정동에 대한 유동인구 데이터가 없습니다."}

#     ppl_row = ppl_row.fillna(0)
#     if not dong:
#         ppl_row["행정동_코드_명"] = ""

#     # store_row 조회
#     store_row_query = store_df.query("자치구_코드_명 == @gu and 서비스_업종_코드_명 == @category")
#     if store_row_query.empty:
#         return {"status": "error", "message": "해당 자치구/업종에 대한 상점 데이터가 없습니다."}

#     store_row = store_row_query.iloc[0]

#     # ------------- 현재 조건 추천 (Single Recommend) -------------
#     base_input = ppl_row.copy()
#     base_input = base_input.apply(lambda row: apply_weight(row, gender, age), axis=1)

#     # 상점 정보 덮어쓰기 (명시적 매핑)
#     base_input["점포_수"] = store_row["점포_수"]
#     base_input["유사_업종_점포_수"] = store_row["유사_업종_점포_수"]
#     base_input["프랜차이즈_점포_수"] = store_row["프랜차이즈_점포_수"]
#     base_input["개업_율"] = store_row["가중_개업_률"]
#     base_input["폐업_률"] = store_row["가중_폐업_률"]
#     base_input["상권_구분_코드_명"] = area_type
#     base_input["서비스_업종_코드_명"] = category

#     df_main = encode(base_input[cols].copy())
#     success_prob = model.predict_proba(df_main)[0][1]
#     single_result = {
#         "success_prob": round(float(success_prob), 4),
#         "recommendation": "추천" if success_prob >= 0.85 else "비추천"
#     }

#     # ------------- 행정동 추천 (Top5 Dong Recommend) -------------
#     dong_df = ppl_df.query("자치구_코드_명 == @gu").copy()
#     dong_df = dong_df.fillna(0)
#     dong_df = dong_df.apply(lambda row: apply_weight(row, gender, age), axis=1)

#     dong_df["점포_수"] = store_row["점포_수"]
#     dong_df["유사_업종_점포_수"] = store_row["유사_업종_점포_수"]
#     dong_df["프랜차이즈_점포_수"] = store_row["프랜차이즈_점포_수"]
#     dong_df["개업_율"] = store_row["가중_개업_률"]
#     dong_df["폐업_률"] = store_row["가중_폐업_률"]
#     dong_df["상권_구분_코드_명"] = area_type
#     dong_df["서비스_업종_코드_명"] = category

#     dong_preds = encode(dong_df[cols].copy())
#     dong_df["성공확률"] = model.predict_proba(dong_preds)[:, 1]
#     dong_df["성공확률"] = dong_df["성공확률"].apply(lambda x: round(float(x), 4))

#     dong_recommend = dong_df[["행정동_코드_명", "성공확률"]] \
#         .sort_values(by="성공확률", ascending=False).head(5).to_dict(orient="records")

#     # ------------- 업종 추천 (Top5 Category Recommend) -------------
#     ppl_base = ppl_df.query("자치구_코드_명 == @gu")
#     if dong:
#         ppl_base = ppl_base.query("행정동_코드_명 == @dong")

#     if ppl_base.empty:
#         return {"status": "error", "message": "해당 조건에 맞는 유동인구 데이터가 없습니다."}

#     ppl_base = ppl_base.iloc[0]
#     ppl_base = apply_weight(ppl_base, gender, age)

#     업종추천 = store_df.query("자치구_코드_명 == @gu").copy()

#     result_list = []
#     for _, row in 업종추천.iterrows():
#         row_data = {
#             "총_유동인구_수": ppl_base["총_유동인구_수"],
#             "남성_유동인구_수": ppl_base["남성_유동인구_수"],
#             "여성_유동인구_수": ppl_base["여성_유동인구_수"],
#             "연령대_20_유동인구_수": ppl_base["연령대_20_유동인구_수"],
#             "연령대_30_유동인구_수": ppl_base["연령대_30_유동인구_수"],
#             "연령대_40_유동인구_수": ppl_base["연령대_40_유동인구_수"],
#             "연령대_50_유동인구_수": ppl_base["연령대_50_유동인구_수"],
#             "점포_수": row["점포_수"],
#             "유사_업종_점포_수": row["유사_업종_점포_수"],
#             "프랜차이즈_점포_수": row["프랜차이즈_점포_수"],
#             "개업_율": row["가중_개업_률"],
#             "폐업_률": row["가중_폐업_률"],
#             "총_직장_인구_수": ppl_base["총_직장_인구_수"],
#             "자치구_코드_명": gu,
#             "행정동_코드_명": dong,
#             "상권_구분_코드_명": area_type,
#             "서비스_업종_코드_명": row["서비스_업종_코드_명"],
#             "X좌표": ppl_base["X좌표"],
#             "Y좌표": ppl_base["Y좌표"]
#         }
#         result_list.append(row_data)

#     업종_df = pd.DataFrame(result_list)
#     업종_preds = encode(업종_df[cols].copy())
#     업종_df["성공확률"] = model.predict_proba(업종_preds)[:, 1]
#     업종_df["성공확률"] = 업종_df["성공확률"].apply(lambda x: round(float(x), 4))

#     category_recommend = 업종_df[["서비스_업종_코드_명", "성공확률"]] \
#         .sort_values(by="성공확률", ascending=False).head(5).to_dict(orient="records")

#     return {
#         "현재조건": single_result,
#         "행정동추천": dong_recommend,
#         "업종추천": category_recommend
#     }