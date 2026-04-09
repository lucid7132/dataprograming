import pandas as pd
import numpy as np

# 파일 경로
file_at_path = 'at_processing_data.csv'
file_nong_path = 'nongnet_processing_data.csv'

# index_col을 지정하여 연도(Category, DATE)를 기준으로 정렬
df_at = pd.read_csv(file_at_path, index_col='Category')
df_nong = pd.read_csv(file_nong_path, index_col='DATE')

# 두 데이터프레임의 인덱스(연도)를 합집합으로 생성 (2013 ~ 2025)
all_years = df_at.index.union(df_nong.index).sort_values()
final_df = pd.DataFrame(index=all_years)

# 컬럼 매핑
column_mapping = {
    '무': '고랭지무',
    '배추': '고랭지배추',
    '깐마늘': '마늘',
    '양파': '양파',
    '사과': '사과'
}

for at_col, nong_col in column_mapping.items():
    # 컬럼 가져오기 (없으면 NaN 처리)
    series_at = df_at[at_col] if at_col in df_at.columns else pd.Series(dtype=float)
    series_nong = df_nong[nong_col] if nong_col in df_nong.columns else pd.Series(dtype=float)
    
    # 연도 기준으로 데이터프레임 합치기
    temp_df = pd.concat([series_at, series_nong], axis=1)
    
    # mean 함수는 NaN을 무시하고 평균
    merged_series = temp_df.mean(axis=1)
    
    # 선형 보간
    interpolated_series = merged_series.interpolate(method='linear', limit_direction='both')
    
    # 결과 추가
    final_df[at_col] = interpolated_series

# 소수점 반올림
final_df = final_df.round(1)
final_df.index.name = 'Year'

# 저장
output_file = 'mix_price.csv'
final_df.to_csv(output_file)

print(final_df.head(15)) # 전체 연도 확인