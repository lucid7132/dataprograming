import pandas as pd
import numpy as np

# 파일 경로 설정 (실제 경로에 맞게 수정 필요할 수 있음)
file_at_path = 'at_processing_data.csv'
file_nong_path = 'nongnet_processing_data.csv'

# 데이터 로드
# index_col을 지정하여 연도(Category, DATE)를 기준으로 정렬
df_at = pd.read_csv(file_at_path, index_col='Category')
df_nong = pd.read_csv(file_nong_path, index_col='DATE')

# 두 데이터프레임의 인덱스(연도)를 합집합으로 생성 (2013 ~ 2025)
all_years = df_at.index.union(df_nong.index).sort_values()
final_df = pd.DataFrame(index=all_years)

# 컬럼 매핑 (AT 데이터 컬럼명 : 농넷 데이터 컬럼명)
column_mapping = {
    '무': '고랭지무',
    '배추': '고랭지배추',
    '깐마늘': '마늘',
    '양파': '양파',
    '사과': '사과'
}

for at_col, nong_col in column_mapping.items():
    # 각 데이터프레임에서 해당 컬럼 가져오기 (없으면 NaN 처리)
    series_at = df_at[at_col] if at_col in df_at.columns else pd.Series(dtype=float)
    series_nong = df_nong[nong_col] if nong_col in df_nong.columns else pd.Series(dtype=float)
    
    # 인덱스(연도) 기준으로 데이터프레임 합치기
    # axis=1로 합쳐서 두 개의 컬럼을 가진 임시 DataFrame 생성
    temp_df = pd.concat([series_at, series_nong], axis=1)
    
    # 1. 값 병합 로직 적용 (mean 함수는 NaN을 무시하고 평균을 구함)
    merged_series = temp_df.mean(axis=1)
    
    # 2. 선형 보간 (Linear Interpolation) 적용
    # limit_direction='both'를 주어 앞뒤 방향 모두 보간
    interpolated_series = merged_series.interpolate(method='linear', limit_direction='both')
    
    # 결과 데이터프레임에 추가
    final_df[at_col] = interpolated_series

# 소수점 첫째 자리 반올림 (가격 데이터이므로 깔끔하게 정리)
final_df = final_df.round(1)

# 인덱스 이름 설정
final_df.index.name = 'Year'

# 결과 저장
output_file = 'mix_price.csv'
final_df.to_csv(output_file)

print(f"병합 및 보간 '{output_file}'")
print("\n[생성된 데이터 미리보기]")
print(final_df.head(15)) # 전체 연도 확인