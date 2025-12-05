import pandas as pd
import numpy as np
import os

# ==========================================
# 1. 설정 및 경로 정의
# ==========================================
# 파일 경로 (사용자 환경에 맞게 확인 필요)
PATH_LAND = "price_land/4개도_농지_실거래가_통합_Clean.csv"
PATH_POP = "Processing_population/data/시도별_귀농가구원수_2013_2024.csv"
PATH_WEATHER = "weather_preprocessing/weather_annual_4provinces.csv"
PATH_CROP = "Processing_Crop/mix_price.csv"

OUTPUT_FILENAME = "final_dataset_for_ai.csv"

# 지역별 주력 작물 정의
REGION_MAIN_CROPS = {
    '강원도': ['무', '배추'],
    '경상남도': ['양파', '깐마늘'],
    '전라남도': ['양파', '깐마늘'],
    '경상북도': ['사과']
}

# 분석 대상 지역 및 연도 범위 설정
TARGET_REGIONS = ['강원도', '경상남도', '경상북도', '전라남도']
START_YEAR = 2015
END_YEAR = 2025

# ==========================================
# 2. 함수 정의
# ==========================================

def preprocess_and_merge():
    print(f"🚀 데이터 병합 및 전처리 시작... ({START_YEAR}~{END_YEAR})")
    print("   (결측치는 0으로 채우지 않고 NaN으로 유지합니다)")

    # -----------------------------------------------------
    # 0) Base Frame 생성 (연도-지역 기준)
    # -----------------------------------------------------
    # 2025년 데이터가 원본에 없더라도 행을 확보하기 위해 기준 프레임 생성
    years = list(range(START_YEAR, END_YEAR + 1))
    base_df = pd.DataFrame([(y, r) for y in years for r in TARGET_REGIONS], columns=['연도', '지역'])
    
    # -----------------------------------------------------
    # 1) Target: 귀농 인구수
    # -----------------------------------------------------
    try:
        df_pop_raw = pd.read_csv(PATH_POP, encoding="cp949")
        df_pop = df_pop_raw[~df_pop_raw['행정구역별'].isin(['행정구역별', '전국'])].copy()
        
        id_vars = ['행정구역별']
        value_vars = [c for c in df_pop.columns if c not in id_vars and c.isdigit()]
        if not value_vars:
             value_vars = [c for c in df_pop.columns if c not in id_vars]

        df_pop_long = df_pop.melt(id_vars=id_vars, value_vars=value_vars, 
                                  var_name='연도', value_name='귀농인구수')
        
        df_pop_long.rename(columns={'행정구역별': '지역'}, inplace=True)
        df_pop_long['연도'] = df_pop_long['연도'].astype(int)
        
        df_pop_long['귀농인구수'] = df_pop_long['귀농인구수'].astype(str).str.replace(',', '', regex=False)
        # errors='coerce'로 변환 실패시 NaN 처리
        df_pop_long['귀농인구수'] = pd.to_numeric(df_pop_long['귀농인구수'], errors='coerce') 
        # 여기서는 원본 데이터의 특성상 숫자로 변환된 후 NaN이 있다면 0이 아닌 그대로 유지하거나,
        # 인구수는 명확한 수치이므로 원본에 값이 있었다면 살리고 없으면 NaN 유지
        
        df_pop_long['지역'] = df_pop_long['지역'].replace({'강원특별자치도': '강원도'})
        
        print(f"   - 인구 데이터 로드 완료")
        
    except Exception as e:
        print(f"❌ 인구 데이터 처리 중 오류: {e}")
        df_pop_long = pd.DataFrame(columns=['연도', '지역', '귀농인구수'])

    # -----------------------------------------------------
    # 2) Feature: 농지 가격
    # -----------------------------------------------------
    try:
        df_land = pd.read_csv(PATH_LAND)
        # 연도, 지역별 평균 계산 (NaN 자동 무시됨)
        df_land_agg = df_land.groupby(['연도', '지역'])['평당단가'].mean().reset_index()
        df_land_agg.rename(columns={'평당단가': '평균지가'}, inplace=True)
        print(f"   - 지가 데이터 로드 완료")
    except Exception as e:
        print(f"❌ 지가 데이터 로드 실패: {e}")
        df_land_agg = pd.DataFrame(columns=['연도', '지역', '평균지가'])

    # -----------------------------------------------------
    # 3) Feature: 기후 데이터
    # -----------------------------------------------------
    try:
        df_weather = pd.read_csv(PATH_WEATHER)
        df_weather.rename(columns={'시도': '지역'}, inplace=True)
        
        cols = ['평균기온', '강수량']
        if 'SPI3' in df_weather.columns:
            cols.append('SPI3')
        
        df_weather_agg = df_weather.groupby(['연도', '지역'])[cols].mean().reset_index()
        print(f"   - 기후 데이터 로드 완료")
    except Exception as E:
        print(f"⚠️ 기후 데이터 로드 실패: {E}")
        df_weather_agg = pd.DataFrame(columns=['연도', '지역', '평균기온', '강수량', 'SPI3'])

    # -----------------------------------------------------
    # 4) Feature: 작물 가격 (YoY 변동률 계산)
    # -----------------------------------------------------
    try:
        try:
            df_crop = pd.read_csv(PATH_CROP, encoding='utf-8')
        except UnicodeDecodeError:
            df_crop = pd.read_csv(PATH_CROP, encoding='cp949')
            
        df_crop.rename(columns={'Year': '연도'}, inplace=True)
        df_crop = df_crop.sort_values('연도')

        crop_cols = [c for c in df_crop.columns if c != '연도']
        
        # 전년 대비 변동률 계산
        df_crop_change = df_crop[['연도']].copy()
        for col in crop_cols:
            df_crop_change[f'작물_{col}_변동률'] = df_crop[col].pct_change() * 100
            
        print(f"   - 작물 데이터 변동률(YoY) 계산 완료")
    except Exception as e:
        print(f"⚠️ 작물 데이터 처리 실패: {e}")
        df_crop_change = pd.DataFrame(columns=['연도'])

    # -----------------------------------------------------
    # 5) 데이터 병합 (Base Frame 기준 Left Join)
    # -----------------------------------------------------
    # Base Frame(2015~2025, 4개 지역)에 데이터를 붙입니다.
    # 데이터가 없는 연도/지역은 자동으로 NaN이 들어갑니다.
    
    main_df = base_df
    
    # 인구 병합
    if not df_pop_long.empty:
        main_df = pd.merge(main_df, df_pop_long, on=['연도', '지역'], how='left')

    # 지가 병합
    if not df_land_agg.empty:
        main_df = pd.merge(main_df, df_land_agg, on=['연도', '지역'], how='left')
    
    # 기후 병합
    if not df_weather_agg.empty:
        main_df = pd.merge(main_df, df_weather_agg, on=['연도', '지역'], how='left')
    
    # 작물 병합 (연도 기준)
    if not df_crop_change.empty:
        main_df = pd.merge(main_df, df_crop_change, on=['연도'], how='left')

    # -----------------------------------------------------
    # 6) 지역별 주력 작물 통합 (NaN 유지)
    # -----------------------------------------------------
    print("\n🌾 지역별 주력 작물 통합(평균) 처리 중...")
    
    final_crop_rates = []
    
    for idx, row in main_df.iterrows():
        region = row['지역']
        main_crops = REGION_MAIN_CROPS.get(region, [])
        
        rates = []
        for crop in main_crops:
            col_name = f'작물_{crop}_변동률'
            # 해당 컬럼이 존재하고 값이 NaN이 아닐 때만 리스트에 추가
            if col_name in row and not pd.isna(row[col_name]):
                rates.append(row[col_name])
        
        if rates:
            # 값이 하나라도 있으면 평균 계산
            final_crop_rates.append(np.mean(rates))
        else:
            # 값이 하나도 없으면(2025년 등) NaN 유지
            final_crop_rates.append(np.nan)
            
    main_df['주력작물_가격변동률'] = final_crop_rates

    # 중요: 결측치 채우기 로직(fillna) 제거됨
    # main_df['주력작물_가격변동률'] = main_df['주력작물_가격변동률'].fillna(0)  <-- 삭제됨

    # 불필요한 개별 작물 컬럼 제거
    cols_to_drop = [c for c in main_df.columns if '작물_' in c and '_변동률' in c]
    main_df.drop(columns=cols_to_drop, inplace=True)
    
    # 저장
    main_df.to_csv(OUTPUT_FILENAME, index=False, encoding='utf-8-sig')
    
    print("\n" + "="*50)
    print(f"🎉 전처리 완료! 파일 저장됨: {OUTPUT_FILENAME}")
    print(f"총 데이터 수: {len(main_df)}행 (2015~2025년 포함)")
    print("="*50)
    print(main_df.tail(10)) # 2025년 데이터 확인을 위해 tail 출력

if __name__ == "__main__":
    preprocess_and_merge()