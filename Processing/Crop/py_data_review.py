import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 한글 폰트 설정
plt.rc('font', family='Malgun Gothic') 
plt.rc('axes', unicode_minus=False)

# ==========================================
# 1. 데이터 로드 및 전처리 함수
# ==========================================
def clean_kosis_csv(file_path, category_name):
    try:
        df = pd.read_csv(file_path, header=[0, 1], encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, header=[0, 1], encoding='cp949')
    
    processed_data = []
    region_col = df.columns[0]
    
    for i, row in df.iterrows():
        region = row[region_col]
        if pd.isna(region) or region in ['시도별', '행정구역별']: continue
        
        if '강원' in region: region = '강원도'
        elif '전라남도' in region: region = '전라남도'
        elif '경상북도' in region: region = '경상북도'
        elif '경상남도' in region: region = '경상남도'
        else: continue

        for col in df.columns[1:]:
            year = col[0]
            var_name = col[1]
            value = row[col]
            
            if isinstance(value, str):
                value = value.replace(',', '').strip()
                if value in ['-', 'X']: value = 0
                else:
                    try: value = float(value)
                    except: value = 0
            
            processed_data.append({
                'Year': int(year),
                'Region': region,
                'Category': category_name,
                'Variable': var_name,
                'Value': float(value)
            })
    return pd.DataFrame(processed_data)

# ==========================================
# 2. 파일 로드 및 통합
# ==========================================
data_dir = 'data'

files = {
    'fruit': os.path.join(data_dir, '과실생산량_성과수미과수.csv'),
    'food': os.path.join(data_dir, '식량작물_생산량_정곡.csv'),
    'root_veg': os.path.join(data_dir, '채소생산량_근채류.csv'),
    'leaf_veg': os.path.join(data_dir, '채소생산량_엽채류.csv'),
    'season_veg': os.path.join(data_dir, '채소생산량_조미채소.csv'),
    'household': os.path.join(data_dir, '재배면적규모별 작물재배 귀농가구.csv')
}

price_file = 'mix_price.csv'

print("데이터 로드 및 처리 중...")
all_crops_df = pd.DataFrame()

for cat, path in files.items():
    if cat == 'household': continue
    if os.path.exists(path):
        temp_df = clean_kosis_csv(path, cat)
        all_crops_df = pd.concat([all_crops_df, temp_df], ignore_index=True)
    else:
        print(f"파일을 찾을 수 없음: {path}")

if os.path.exists(files['household']):
    household_df = clean_kosis_csv(files['household'], 'Return_Farm')
    household_total = household_df[household_df['Variable'].str.contains('재배가구')].copy()
    household_total.rename(columns={'Value': 'Households'}, inplace=True)
    household_total['Region'] = household_total['Region'].replace('강원특별자치도', '강원도')
    household_total = household_total.groupby(['Year', 'Region'])['Households'].max().reset_index()
else:
    household_total = pd.DataFrame(columns=['Year', 'Region', 'Households'])

if not all_crops_df.empty:
    df_pivot = all_crops_df.pivot_table(index=['Year', 'Region'], columns='Variable', values='Value', aggfunc='mean').reset_index()
    master_df = pd.merge(df_pivot, household_total, on=['Year', 'Region'], how='left')
    master_df = master_df[master_df['Year'] >= 2015]
    master_df.fillna(0, inplace=True)
else:
    master_df = pd.DataFrame()
    print("생산량 데이터가 비어있습니다.")

# ==========================================
# 3. 가격 데이터 반영 및 시각화 (수정됨)
# ==========================================

if os.path.exists(price_file) and not master_df.empty:
    print("\n--- 가격 데이터 로드 및 병합 ---")
    price_df = pd.read_csv(price_file)
    if 'DATE' in price_df.columns:
        price_df.rename(columns={'DATE': 'Year'}, inplace=True)
    
    # 2024년 데이터까지 사용
    price_df = price_df[price_df['Year'] <= 2024]
    master_df = pd.merge(master_df, price_df, on='Year', how='left')
    
    # [수정] 마늘의 prod_keyword를 '깐마늘' -> '마늘'로 변경
    target_crops_mapping = {
        '강원_고랭지배추': {'prod_keyword': '배추', 'price_col': '배추'},
        '강원_고랭지무': {'prod_keyword': '무', 'price_col': '무'},
        '경북_사과': {'prod_keyword': '사과', 'price_col': '사과'},
        '남부_양파': {'prod_keyword': '양파', 'price_col': '양파'},
        '남부_마늘': {'prod_keyword': '마늘', 'price_col': '깐마늘'} 
    }
    
    plot_data = {} 
    
    print("\n--- 연도별 실제 가격 반영 매출액 계산 ---")
    for label, info in target_crops_mapping.items():
        prod_keyword = info['prod_keyword']
        price_col = info['price_col']
        
        # 생산량 컬럼 찾기
        prod_cols = [c for c in master_df.columns if prod_keyword in c and '10a당 생산량' in c]
        
        if prod_cols and price_col in master_df.columns:
            col_name = prod_cols[0]
            revenue_col = f'{label}_매출(천원)'
            # 매출액 계산 (kg/10a * 원/kg / 1000 = 천원/10a)
            master_df[revenue_col] = master_df[col_name] * master_df[price_col] / 1000
            
            # 시각화를 위해 생산량 컬럼과 매출액 컬럼을 모두 저장
            plot_data[label] = {
                'production': col_name,
                'revenue': revenue_col
            }
            print(f"[계산 완료] {label}: 생산량({col_name}) * 가격({price_col})")
        else:
            print(f"[스킵] {label}: 생산량 컬럼({prod_keyword} 포함) 또는 가격 컬럼({price_col})을 찾을 수 없음")

    # -------------------------------------------------------
    # 그래프 그리기 (1행 3열)
    # 1열: 10a당 생산량, 2열: 매출액(가격결합), 3열: 귀농가구
    # -------------------------------------------------------
    if plot_data and 'Households' in master_df.columns:
        fig, axes = plt.subplots(1, 3, figsize=(24, 8)) # 1행 3열로 변경
        
        colors = sns.color_palette("husl", len(plot_data))
        
        # 공통: 지역 필터링 함수
        def get_plot_df(df, label):
            region_filter = label.split('_')[0]
            region_name = None
            if region_filter == '강원': region_name = '강원도'
            elif region_filter == '경북': region_name = '경상북도'
            # 남부 등 기타는 전체 평균 혹은 필터링 없음
            
            if region_name:
                return df[df['Region'] == region_name]
            return df

        # --- [1열] 10a당 생산량 그래프 ---
        for i, (label, cols) in enumerate(plot_data.items()):
            prod_col = cols['production']
            temp_df = master_df[master_df[prod_col] > 0]
            plot_df = get_plot_df(temp_df, label)
            
            # 연도별 평균
            plot_df = plot_df.groupby('Year')[prod_col].mean().reset_index()
            
            sns.lineplot(data=plot_df, x='Year', y=prod_col, label=label, 
                         marker='o', linewidth=2.5, color=colors[i], ax=axes[0])
        
        axes[0].set_title('10a당 품목별 생산량 추이 (가격 반영 전)', fontsize=15)
        axes[0].set_ylabel('생산량 (kg/10a)', fontsize=12)
        axes[0].grid(True, linestyle='--', alpha=0.6)
        axes[0].legend(title='작물', fontsize=10)

        # --- [2열] 예상 매출액 그래프 (가격 결합) ---
        for i, (label, cols) in enumerate(plot_data.items()):
            rev_col = cols['revenue']
            temp_df = master_df[master_df[rev_col] > 0]
            plot_df = get_plot_df(temp_df, label)
            
            plot_df = plot_df.groupby('Year')[rev_col].mean().reset_index()
            
            sns.lineplot(data=plot_df, x='Year', y=rev_col, label=label, 
                         marker='o', linewidth=2.5, color=colors[i], ax=axes[1])
        
        axes[1].set_title('연도별 가격을 반영한 10a당 예상 매출액', fontsize=15)
        axes[1].set_ylabel('예상 매출액 (천원/10a)', fontsize=12)
        axes[1].grid(True, linestyle='--', alpha=0.6)
        axes[1].legend(title='작물', fontsize=10)

        # --- [3열] 귀농 가구 수 그래프 ---
        household_plot_df = master_df[master_df['Year'] <= 2024]
        sns.lineplot(data=household_plot_df, x='Year', y='Households', hue='Region', 
                     marker='o', linewidth=2.5, errorbar=None, ax=axes[2])
        axes[2].set_title('연도별 지역별 귀농 가구 수 변화', fontsize=15)
        axes[2].set_ylabel('귀농 가구 수', fontsize=12)
        axes[2].grid(True, linestyle='--', alpha=0.7)

        plt.tight_layout()
        plt.show()
        print("3개의 그래프 출력 완료")

else:
    print("가격 파일이 없거나 마스터 데이터가 비어 있어 처리를 중단합니다.")