import pandas as pd
from functools import reduce
import glob
import os

# ==========================================
# 1. fath_dir 경로 내의 모든 csv 파일 로드
# ==========================================
fath_dir = 'data' # 데이터 폴더 경로

pd.set_option('display.max_columns', 5)
file_paths = glob.glob(os.path.join(fath_dir, "*.csv"))

print(f"찾은 파일 개수: {len(file_paths)}개")
print("파일 목록:", file_paths)

data_file = {} # {파일 이름: 데이터}
for path in file_paths:
    file_name = os.path.basename(path)
    print(f"\n--- {file_name} 로딩 중... ---")
    try:
        df = pd.read_csv(path,header=[0,1], encoding='cp949')
        # print(df.head())# 데이터 미리보기
        data_file[file_name] = df
        
    except Exception as e:
        print(f"실패: {e}")


# ==========================================
# 2. 데이터 정리 및 병합 함수 정의
# ==========================================

region_mapping = {
    '강원특별자치도': '강원도',
    '강원도': '강원도',
    '전라남도': '전라남도',
    '경상북도': '경상북도',
    '경상남도': '경상남도'
}

for file_name, df in data_file.items():

    new_cols = []
    for col in df.columns:
        year = str(col[0]).split('.')[0] 
        detail = str(col[1])
        if "행정구역별" in year or "시도별" in year or "구분" in year:
            new_cols.append("Region")
        else:
            clean_detail = detail.replace(':', '_').replace('(', '').replace(')', '').replace(' ', '')
            new_cols.append(f"{year}_{clean_detail}")
    
    df.columns = new_cols
    
    # Melt (Wide -> Long 변환)
    df_melted = pd.melt(df, id_vars=['Region'], var_name='Year_Var', value_name='Value')
    
    # 연도와 변수 분리
    # 예: "2020_사과_생산량" -> Year=2020, Var="사과_생산량"
    df_melted[['Year', 'Variable']] = df_melted['Year_Var'].str.split('_', n=1, expand=True)
    
    # Pivot (변수들을 컬럼으로 올림)
    df_final = df_melted.pivot_table(
        index=['Year', 'Region'], 
        columns='Variable', 
        values='Value', 
        aggfunc='first'
    ).reset_index()
    
    # 지역명 표준화 적용
    df_final['Region'] = df_final['Region'].map(region_mapping).fillna(df_final['Region'])
    
    # 컬럼명 앞에 접두사 붙이기 (어떤 데이터 출처인지 알기 위해)
    rename_map = {col: f"{file_name}_{col}" for col in df_final.columns if col not in ['Year', 'Region']}
    df_final = df_final.rename(columns=rename_map)
    
    data_file[file_name] = df_final

# ==========================================
# 실제 파일 처리 및 병합 실행
# ==========================================

df_list = list(data_file.values())

df_master = reduce(lambda left, right: pd.merge(left, right, on=['Year', 'Region'], how='outer'), df_list)


# 6. CSV로 저장 (분석용)
try :
    df_master.to_csv("Final_Master_Dataset.csv", index=False, encoding='cp949')
    print("데이터 전처리 완료")
except Exception as e:
    print(f"저장 실패: {e}")