import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. [자동 생성] 2025년 2분기 최신 데이터(가격/거래량) 파일 만들기
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
    print(f"[System] '{file_name}' 파일이 생성되었습니다.")
    return file_name

# ==========================================
# 2. 데이터 로드 함수들
# ==========================================

def get_latest_data(file_path):
    print(f"[1/3] 2025년 2분기 최신 농지 데이터 로드 중...")
    try:
        df = pd.read_csv(file_path)
        
        def clean_province(x):
            x = str(x).replace(" ", "")
            mapping = {
                "경기": "경기도", "강원": "강원도", "충북": "충청북도", "충남": "충청남도",
                "전북": "전라북도", "전남": "전라남도", "경북": "경상북도", "경남": "경상남도",
                "제주": "제주도", "세종": "세종특별자치시", "특광역": "특별시/광역시"
            }
            return mapping.get(x, x)

        df['Province'] = df['Province'].apply(clean_province)
        df = df[~df['Province'].isin(['전국'])] 
        df = df.rename(columns={'Plots': 'Total_Volume'}) 
        
        return df[['Province', 'BasePrice', 'Total_Volume']]
    except Exception as e:
        print(f"   [Error] 최신 데이터 파일 읽기 실패: {e}")
        return pd.DataFrame(columns=['Province', 'BasePrice', 'Total_Volume'])

def get_fluctuation_data(file_path):
    print(f"[2/3] 지가 변동률 데이터 로드 중...")
    try:
        try: df = pd.read_csv(file_path, encoding="cp949")
        except: df = pd.read_csv(file_path, encoding="utf-8")

        df = df[df["항목"] == "지가변동률[%]"].copy()
        
        # 날짜 컬럼 중 가장 최신 데이터 추출 (9월 데이터 자동 인식)
        month_cols = [c for c in df.columns if "월" in str(c)]
        def parse_date(c):
            digits = "".join(filter(str.isdigit, c))
            return int(digits) if digits else 0
        recent_col = sorted(month_cols, key=parse_date)[-1]
        
        print(f"   -> 확인된 최신 변동률 시점: {recent_col}") # 확인용 로그 출력

        df["City"] = df["시군구별"].astype(str).str.strip()
        df = df[~df["City"].isin(["전국"]) & ~df["City"].str.endswith("도")]
        df["GrowthRate"] = pd.to_numeric(df[recent_col], errors="coerce")
        
        return df[["City", "GrowthRate"]]
    except Exception as e:
        print(f"   [Error] 지가 변동률 파일 읽기 실패: {e}")
        return pd.DataFrame(columns=["City", "GrowthRate"])

def get_area_data(file_path):
    print(f"[3/3] 경지(밭) 면적 데이터 로드 중...")
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
    f_latest = create_latest_csv()
    f_fluctuation = "시군구별용도지역별이용상황별 지가변동률.csv"
    f_area = "시군별_논밭별_경지면적_20251107103537.csv"

    # 데이터 로드
    df_latest = get_latest_data(f_latest)
    df_f = get_fluctuation_data(f_fluctuation)
    df_a = get_area_data(f_area)

    # 데이터 통합
    area_growth = pd.merge(df_a, df_f, on="City", how="left")
    prov_stats = area_growth.groupby("Province")[["FieldArea", "GrowthRate"]].mean().reset_index()
    final_df = pd.merge(df_latest, prov_stats, on="Province", how="left")

    # 정렬
    final_df = final_df.sort_values("BasePrice", ascending=False)

    print("\n[Result] 시도별 최신 지표 집계 완료")
    print(final_df)

    # 시각화 (팩트에 기반하여 수정됨)
    metrics = [
        ("BasePrice", "평균 농지가격 (원/㎡)", "2025년 2분기 실거래가 기준"),
        ("GrowthRate", "평균 지가 변동률 (%)", "2025년 9월 기준"), # [수정] 팩트에 맞게 9월로 변경
        ("FieldArea", "평균 밭 경지면적 (ha)", "2025년 11월 기준"),
        ("Total_Volume", "총 거래 필지 수 (건)", "2025년 2분기 실거래 신고 기준")
    ]

    for col, title, period in metrics:
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        sub_data = final_df[["Province", col]].dropna().sort_values(by=col, ascending=False)
        
        if sub_data.empty:
            ax.text(0.5, 0.5, "데이터 없음", ha='center', va='center')
            ax.set_title(f"시도별 {title}\n({period})")
            plt.tight_layout()
            plt.show()
            continue

        colors = ["crimson" if "강원" in str(idx) else "lightgray" for idx in sub_data["Province"]]
        
        bars = ax.bar(sub_data["Province"], sub_data[col], color=colors)
        
        ax.set_title(f"시도별 {title}\n({period})", fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        
        for bar, province in zip(bars, sub_data["Province"]):
            if "강원" in str(province):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height, 
                        f"{height:,.1f}", 
                        ha='center', va='bottom', color='red', fontweight='bold', fontsize=12)

        plt.tight_layout()
        plt.show()

    print("완료: 2025년 9월 변동률 데이터를 반영한 그래프 생성 끝.")

if __name__ == "__main__":
    main()