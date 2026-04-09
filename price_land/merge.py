import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import platform

# ==========================================
# 설정 영역
# ==========================================
DATA_ROOT = "data"  # 최상위 데이터 폴더
REGIONS = ["강원도", "경상남도", "경상북도", "전라남도"]  # 대상 지역
FILE_SUFFIX_START = 1
FILE_SUFFIX_END = 11

# 결과 파일명 설정
OUTPUT_FILENAME_MAIN = "4개도_농지_실거래가_통합_Clean.csv"
OUTPUT_FILENAME_PIVOT = "4개도_연도별_지역별_평균지가.csv"

# ==========================================
# 1. 데이터 처리 및 병합 (ETL)
# ==========================================

def get_header_index(file_path):
    """CSV 파일 내에서 실제 헤더 위치 찾기"""
    try:
        with open(file_path, 'r', encoding='cp949') as f:
            for i, line in enumerate(f):
                if '시군구' in line and '거래금액' in line:
                    return i
    except Exception:
        return -1
    return -1

def process_and_merge_data():
    all_data = []
    print(f"🚀 4개 지역 ({', '.join(REGIONS)}) 데이터 병합 시작...")

    for region in REGIONS:
        region_dir = os.path.join(DATA_ROOT, region)
        print(f"\n📂 [{region}] 처리 중...")
        
        if not os.path.exists(region_dir):
            print(f"   ⚠️ 폴더 없음: {region_dir} (건너뜀)")
            continue

        for i in range(FILE_SUFFIX_START, FILE_SUFFIX_END + 1):
            file_name = f"{region} 토지 가격 ({i}).csv"
            file_path = os.path.join(region_dir, file_name)
            
            if not os.path.exists(file_path):
                continue

            header_row = get_header_index(file_path)
            if header_row == -1:
                continue

            try:
                # 데이터 로드
                df = pd.read_csv(file_path, encoding='cp949', skiprows=header_row)
                
                # 1. 필수 컬럼 선택 (시군구 제외 요청 반영)
                required_cols = ['지목', '계약년월', '계약면적', '거래금액(만원)']
                available_cols = [c for c in required_cols if c in df.columns]
                df = df[available_cols]

                # 2. 거래금액 전처리
                if '거래금액(만원)' in df.columns:
                    df['거래금액(만원)'] = df['거래금액(만원)'].astype(str).str.replace(',', '').astype(float)
                
                # 3. 농지(전/답/과수원) 필터링
                if '지목' in df.columns:
                    target_jimok = ['전', '답', '과수원']
                    df = df[df['지목'].isin(target_jimok)]

                # 4. 지역 컬럼 추가
                df['지역'] = region
                
                # 5. 연도 추출
                df['연도'] = df['계약년월'].astype(str).str[:4].astype(int)

                # 6. 평당단가 계산
                df = df[df['계약면적'] > 0] 
                df['평당단가'] = df['거래금액(만원)'] / (df['계약면적'] / 3.3058)
                df['평당단가'] = df['평당단가'].round(1)

                all_data.append(df)

            except Exception as e:
                print(f"   ❌ 에러 발생: {file_name} - {e}")

    if not all_data:
        print("❌ 처리할 데이터가 없습니다.")
        return None

    # 전체 병합
    merged_df = pd.concat(all_data, ignore_index=True)
    
    # 컬럼 정리 (시군구 제거됨)
    final_cols = ['연도', '지역', '지목', '평당단가', '거래금액(만원)', '계약면적']
    merged_df = merged_df[final_cols].sort_values(by=['연도', '지역'])

    # 메인 통합 파일 저장
    merged_df.to_csv(OUTPUT_FILENAME_MAIN, index=False, encoding='utf-8-sig')
    
    print("\n" + "="*50)
    print(f"🎉 1. 통합 파일 생성 완료: {OUTPUT_FILENAME_MAIN}")
    print(f"   총 거래 내역 수: {len(merged_df):,}건")
    
    return merged_df

# ==========================================
# 2. 연도별 지역별 평균지가 요약 (Pivot)
# ==========================================

def create_price_summary(df):
    print("\n📊 2. 연도별/지역별 평균 지가 집계 중...")
    
    # Pivot Table 생성 (Index: 연도, Columns: 지역, Values: 평당단가 평균)
    pivot_df = df.pivot_table(index='연도', columns='지역', values='평당단가', aggfunc='mean')
    
    # 소수점 1자리 반올림
    pivot_df = pivot_df.round(1)
    
    # 결측치(NaN)는 0으로 채움 (보간 X)
    pivot_df = pivot_df.fillna(0)
    
    # 컬럼 순서 지정 (가나다 순 혹은 지정한 순서)
    desired_order = ["강원도", "경상남도", "경상북도", "전라남도"]
    # 실제 데이터에 존재하는 컬럼만 선택하여 정렬
    existing_cols = [col for col in desired_order if col in pivot_df.columns]
    pivot_df = pivot_df[existing_cols]

    # 저장 (index=True를 해야 '연도'가 포함됨)
    pivot_df.to_csv(OUTPUT_FILENAME_PIVOT, encoding='utf-8-sig')
    
    print(f"🎉 요약 파일 생성 완료: {OUTPUT_FILENAME_PIVOT}")
    print("="*50)
    print(pivot_df.head(10)) # 미리보기 출력
    print("="*50)

# ==========================================
# 3. 시각화 함수 (Visualization)
# ==========================================

def set_korean_font():
    system_name = platform.system()
    if system_name == 'Windows':
        plt.rc('font', family='Malgun Gothic')
    elif system_name == 'Darwin':
        plt.rc('font', family='AppleGothic')
    else:
        plt.rc('font', family='NanumGothic')
    plt.rc('axes', unicode_minus=False)

def visualize_comparison(df):
    if df is None or df.empty:
        return

    # [조건] 2015년 이후 데이터만 필터링하여 시각화
    viz_df = df[df['연도'] >= 2015].copy()
    
    print(f"\n📈 시각화 생성 중 (2015년 이후 데이터 기준)...")
    
    set_korean_font()
    fig, axes = plt.subplots(3, 1, figsize=(16, 24))
    
    # 1. 평당 평균가격 추이
    sns.lineplot(data=viz_df, x='연도', y='평당단가', hue='지역', 
                 marker='o', palette='Set1', ax=axes[0], linewidth=3)
    axes[0].set_title('1. 4개도 농지 평당 평균가격 추이 (2015~)', fontsize=18, fontweight='bold')
    axes[0].set_ylabel('평당 가격 (만원)')
    axes[0].grid(True, linestyle='--', alpha=0.6)
    axes[0].set_xticks(range(2015, viz_df['연도'].max() + 1))

    # 2. 가격 분포 (Boxplot)
    sns.boxplot(data=viz_df, x='지역', y='평당단가', hue='연도', 
                showfliers=False, palette='viridis', ax=axes[1])
    axes[1].set_title('2. 지역별/연도별 가격 분포 (이상치 제외)', fontsize=18, fontweight='bold')
    axes[1].set_ylabel('평당 가격 (만원)')
    axes[1].grid(True, axis='y', linestyle='--', alpha=0.6)

    # 3. 거래량 추이
    count_data = viz_df.groupby(['연도', '지역']).size().reset_index(name='거래건수')
    sns.barplot(data=count_data, x='연도', y='거래건수', hue='지역', 
                palette='Set2', alpha=0.9, ax=axes[2])
    axes[2].set_title('3. 연도별/지역별 농지 거래량 추이', fontsize=18, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('4개도_지가분석_최종결과.png', dpi=300)
    print("🎉 시각화 이미지 저장 완료: '4개도_지가분석_최종결과.png'")
    plt.show()

# ==========================================
# 실행부
# ==========================================
if __name__ == "__main__":
    # 1. 데이터 통합 및 Clean 파일 생성
    merged_dataframe = process_and_merge_data()
    
    if merged_dataframe is not None:
        # 2. 연도별/지역별 평균지가 Pivot 파일 생성 (추가된 기능)
        create_price_summary(merged_dataframe)
        
        # 3. 시각화
        visualize_comparison(merged_dataframe)