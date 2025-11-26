import pandas as pd
import re
import os

folder_path = "data/price_nongnet" # 데이터 폴더 경로
#------------------------------
# 농넷 도소매 조사 가격 데이터
#------------------------------

# float 형식으로 형변환
def clean_price(x):
    if isinstance(x, str):
        return float(x.replace(',', ''))
    return float(x)

# 거래 단위 변환 (예: "20kg" -> 20.0)
def extract_weight(unit_str):
    match = re.search(r'(\d+)', str(unit_str))
    if match:
        return float(match.group(1))
    return 1.0

# 3. 개별 파일 처리 및 결측치 처리 로직
def process_agricultural_data(file_name, item_name):
    full_path = os.path.join(folder_path, file_name)
    
    # 파일 존재 여부 확인
    if not os.path.exists(full_path):
        print(f"파일을 찾을 수 없습니다: {full_path}")
        print(f"   (현재 실행 위치: {os.getcwd()})")
        return None

    df = pd.read_csv(full_path)

    # 1. 데이터 전처리
    df['평균가격'] = df['평균가격'].apply(clean_price) # 모든 가격 데이터 float으로 형변환
    df = df[df['등급'] == '상품'] # '상품' 등급만 사용
    df['weight_kg'] = df['거래단위'].apply(extract_weight)
    df['price_per_kg'] = df['평균가격'] / df['weight_kg'] # 키로당 가격
    
    # 2. 연도별 평균 계산
    df_yearly = df.groupby('DATE')['price_per_kg'].mean().sort_index()

    full_index = pd.Index(range(2013, 2025), name='DATE')

    price_series = df_yearly.reindex(full_index).rename(item_name)
    
    # rate 계산 로직 삭제됨
    
    # 결과 Series 반환 (리스트가 아닌 단일 Series 반환)
    return price_series 


files = {
    '고랭지 무.csv': '고랭지무',
    '고랭지 배추.csv': '고랭지배추',
    '마늘.csv': '마늘',
    '사과.csv': '사과',
    '양파.csv': '양파'
}

results = []

print(f"데이터 폴더 경로: {os.path.abspath(folder_path)}\n")

for file_path, column_name in files.items():
    print(f"Processing {file_path}...")
    series = process_agricultural_data(file_path, column_name)
    if series is not None:
        results.append(series) # 리스트 extend가 아닌 append로 변경

# 결과 저장
if results:
    final_df = pd.concat(results, axis=1)
    # rate 컬럼 포맷팅 로직 삭제됨
    
    # 결과 파일은 실행 위치에 저장됩니다.
    output_file = 'nongnet_processing_data.csv'
    final_df.to_csv(output_file, float_format='%.1f')
    print(f"\n완료 '{output_file}'")
else:
    print("\n처리된 데이터가 없습니다. 'data/nongnet' 폴더 안에 파일이 있는지 확인해주세요.")