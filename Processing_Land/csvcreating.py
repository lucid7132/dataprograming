import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import io

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. [자동 생성] 2025년 최신 데이터 파일 만들기
# ==========================================
def create_latest_csv():
    csv_content = """Province,BasePrice,Plots
전 국,53322,41241
특광역,121449,230
경 기,177514,5391
강 원,42923,3274
충 북,51636,3179
충 남,42306,5901
전 북,32938,4607
전 남,25610,7528
경 북,37780,6340
경 남,46910,4242
제 주,124030,549"""
    
    file_name = "2025_Q2_Latest_Price.csv"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(csv_content)
    print(f"[System] '{file_name}' 파일이 자동으로 생성되었습니다.")
    return file_name

# ==========================================
# 2. 데이터 로드 및 분석 함수들
# ==========================================

def get_latest_data(file_path):
    print(f"[1/3] 2025년 2분기 최신 농지 데이터 로드 중... ({file_path})")
    try:
        df = pd.read_csv(file_path)
        
        # 지역명 정제 ("강 원" -> "강원도")
        def clean_province(x):
            x = str(x).replace(" ", "")
            mapping = {
                "경기": "경기도", "강원": "강원도", "충북": "충청북도", "충남": "충청남도",
                "전북": "전라북도", "전남": "전라남도", "경북": "경상북도", "경남": "경상남도",
                "제주": "제주도", "세종": "세종특별자치시", "특광역": "특별시/광역시"
            }
            return mapping.get(x, x)

        df['Province'] = df['Province'].apply(clean_province)
        
        # 전국, 특광역 등 불필요한 행 제외 (필요시 '특광역'은 포함 가능)
        df = df[~df['Province'].isin(['전국'])]
        
        # 컬럼명 통일 (Plots -> Total_Volume)
        df = df.rename(columns={'Plots': 'Total_Volume'})
        
        return df[['Province', 'BasePrice', 'Total_Volume']]
    except Exception as e:
        print(f"   [Error] 최신 데이터 파일 읽기 실패: {e}")
        return pd.DataFrame(columns=['Province', 'BasePrice', 'Total_Volume'])

def get_fluctuation_data(file_path):
    print(f"[2/3] 지가 변동률 데이터 로드 중... ({file_path})")
    try:
        try: df = pd.read_csv(file_path, encoding="cp949")
        except: df = pd.read_csv(file_path, encoding="utf-8")

        df = df[df["항목"] == "지가변동률[%]"].copy()
        month_cols = [c for c in df.columns if "월" in str(c)]
        if not month_cols: return pd.DataFrame(columns=["City", "GrowthRate"])

        def parse_date(c):
            digits = "".join(filter(str.isdigit, c))
            return int(digits) if digits else 0
        
        recent_col = sorted(month_cols, key=parse_date)[-1]
        df["City"] = df["시군구별"].astype(str).str.strip()
        df = df[~df["City"].isin(["전국"]) & ~df["City"].str.endswith("도")]
        df["GrowthRate"] = pd.to_numeric(df[recent_col], errors="coerce")
        
        return df[["City", "GrowthRate"]]
    except Exception as e:
        print(f"   [Error] 지가 변동률 파일 읽기 실패: {e}")
        return pd.DataFrame(columns=["City", "GrowthRate"])

def get_area_data(file_path):
    print(f"[3/3] 경지(밭) 면적 데이터 로드 중... ({file_path})")
    try:
        try: df = pd.read_csv(file_path, encoding="cp949")
        except: df = pd.read_csv(file_path, encoding="utf-8")

        df = df[2:].reset_index(drop=True)
        province_map = {"강원": "강원도", "전남": "전라남도", "경북": "경상북도", "경남": "경상남도"}

        df["City"] = df.iloc[:, 1].astype(str).str.strip()
        df = df[df["City"] != "소계"]
        df["Province"] = df.iloc[:, 0].astype(str).str.strip().map(province_map).fillna(df.iloc[:, 0])
        df["FieldArea"] = df.iloc[:, 16].astype(str).str.replace(" ", "").str.replace(",", "").apply(pd.to_numeric, errors="coerce")

        return df[["Province", "City", "FieldArea"]].dropna()
    except Exception as e:
        print(f"   [Error] 경지면적 파일 읽기 실패: {e}")
        return pd.DataFrame(columns=["Province", "City", "FieldArea"])

# ==========================================
# 3. 메인 실행 함수
# ==========================================
def main():
    # 1. 최신 데이터 파일 생성 (자동)
    f_latest = create_latest_csv()
    
    # 2. 나머지 파일명 정의 (기존 파일 사용)
    f_fluctuation = "시군구별용도지역별이용상황별 지가변동률.csv"
    f_area = "시군별_논밭별_경지면적_20251107103537.csv"

    # 3. 데이터 로드
    df_latest = get_latest_data(f_latest) # Province 단위 (가격, 거래량)
    df_f = get_fluctuation_data(f_fluctuation) # City 단위 (변동률)
    df_a = get_area_data(f_area) # Province, City 단위 (면적)

    # 4. 데이터 통합 (도별 평균 산출)
    # (1) 면적 데이터에 변동률 데이터를 City 기준으로 병합
    area_growth = pd.merge(df_a, df_f, on="City", how="left")
    
    # (2) 도별(Province)로 그룹화하여 평균 계산
    prov_stats = area_growth.groupby("Province")[["FieldArea", "GrowthRate"]].mean().reset_index()
    
    # (3) 최신 가격/거래량 데이터(이미 도별)와 병합
    final_df = pd.merge(df_latest, prov_stats, on="Province", how="left")

    # 5. 정렬 (가격 기준 내림차순)
    final_df = final_df.sort_values("BasePrice", ascending=False)

    print("\n[Result] 시도별 최신 지표 집계 완료")
    print(final_df)

    # 6. 시각화 (개별 그래프 출력 및 시점 명시)
    metrics = [
        ("BasePrice", "평균 농지가격 (원/㎡)", "2025년 2분기 실거래가 기준"),
        ("GrowthRate", "평균 지가 변동률 (%)", "2023년 기준 (최신 월)"),
        ("FieldArea", "평균 밭 경지면적 (ha)", "2025년 11월 기준"),
        ("Total_Volume", "총 거래 필지 수 (건)", "2025년 2분기 실거래 신고 기준")
    ]

    for col, title, period in metrics:
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        # 데이터 정렬 및 추출
        sub_data = final_df[["Province", col]].dropna().sort_values(by=col, ascending=False)
        
        if sub_data.empty:
            ax.text(0.5, 0.5, "데이터 없음", ha='center', va='center')
            ax.set_title(f"시도별 {title}\n({period})")
            plt.tight_layout()
            plt.show()
            continue

        # 색상 설정 (강원도 강조)
        colors = ["crimson" if "강원" in str(idx) else "lightgray" for idx in sub_data["Province"]]
        
        bars = ax.bar(sub_data["Province"], sub_data[col], color=colors)
        
        # 제목에 시점 정보 포함
        ax.set_title(f"시도별 {title}\n({period})", fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        
        # 강원도 값 텍스트 표시
        for bar, province in zip(bars, sub_data["Province"]):
            if "강원" in str(province):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height, 
                        f"{height:,.1f}", 
                        ha='center', va='bottom', color='red', fontweight='bold', fontsize=12)

        plt.tight_layout()
        plt.show()

    print("완료: 4개의 최신 데이터 반영 그래프 생성 끝.")

if __name__ == "__main__":
    main()