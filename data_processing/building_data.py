import csv
import pandas as pd

## 매장용빌딩의 경우 사이트내 csv파일 다운
file_path = "매장용빌딩_임대료공실률수익률.csv"

# 1. CSV 파일 안전하게 읽기
rows = []
with open(file_path, encoding='utf-8', errors='ignore') as f:
    reader = csv.reader(f, quotechar='"')
    for row in reader:
        rows.append(row)

df = pd.DataFrame(rows[1:], columns=rows[0])

# 2. 컬럼명 정제
df.columns = [col.strip().replace('"', '').replace('\ufeff', '') for col in df.columns]

# 3. 열 나누기
id_vars = ['지역별', '구분별', '항목', '단위']
value_vars = [col for col in df.columns if col not in id_vars and col.strip() != '']

# 4. melt
df_melted = df.melt(id_vars=id_vars, value_vars=value_vars,
                    var_name='기간', value_name='값')

# 5. 연도 / 분기 분리
df_melted[['연도', '분기']] = df_melted['기간'].str.extract(r'(\d{4})\.\s*(\d)/4')
df_melted.drop(columns=['기간'], inplace=True)

# 6. 값 숫자형으로 변환
df_melted['값'] = pd.to_numeric(df_melted['값'].str.replace(',', ''), errors='coerce')

# 7. 컬럼명 한글로 정리
df_melted.columns = ['지역', '구분', '항목', '단위', '값', '연도', '분기']

# 8. 저장도 가능
df_melted.to_csv("전처리_매장용빌딩_임대료공실률수익률.csv", index=False)

# df_melted
