import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import re

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 유틸리티 함수
# ==========================================
def check_file_exists(file_path):
    if not os.path.exists(file_path):
        print(f"   [Warning] 파일이 존재하지 않습니다: {file_path}")
        return False
    return True

# ==========================================
# 1. [데이터 생성] 2025년 2분기 최신 데이터
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
    return file_name

# ==========================================
# 2. 데이터 로드 함수들
# ==========================================
def get_latest_data(file_path):
    if not check_file_exists(file_path):
        return pd.DataFrame(columns=['Province', 'BasePrice', 'Total_Volume'])
    
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
        
        return df[['Province', 'BasePrice', 'Total_Volume']].copy()
    except Exception as e:
        return pd.DataFrame()

def get_fluctuation_data(file_path):
    # 이 함수는 '표'를 만들기 위해 최신 데이터 1개만 가져옴
    if not check_file_exists(file_path):
        return pd.DataFrame(columns=["City", "GrowthRate"])
    
    try:
        try: df = pd.read_csv(file_path, encoding="cp949")
        except: df = pd.read_csv(file_path, encoding="utf-8")
        
        if "항목" in df.columns:
            df = df[df["항목"] == "지가변동률[%]"].copy()
        
        date_cols = []
        pattern = re.compile(r'(\d{4})[\.\년/\-\s]+(\d{1,2})')
        
        for col in df.columns:
            if pattern.search(str(col)):
                date_cols.append(col)
                
        if not date_cols:
            return pd.DataFrame(columns=["City", "GrowthRate"])

        recent_col = date_cols[-1]
        
        city_col = [c for c in df.columns if "시군구" in c or "지역" in c][0]
        
        df["City"] = df[city_col].astype(str).str.strip()
        df = df[~df["City"].isin(["전국"]) & ~df["City"].str.endswith("도")]
        df["GrowthRate"] = pd.to_numeric(df[recent_col], errors="coerce")
        
        return df[["City", "GrowthRate"]].dropna()
    except Exception as e:
        return pd.DataFrame()

def get_area_data(file_path):
    if not check_file_exists(file_path):
        return pd.DataFrame(columns=["Province", "City", "FieldArea"])
    
    try:
        try: df = pd.read_csv(file_path, encoding="cp949")
        except: df = pd.read_csv(file_path, encoding="utf-8")
        
        df = df[2:].reset_index(drop=True)
        province_map = {
            "강원": "강원도", "전남": "전라남도", "경북": "경상북도", "경남": "경상남도",
            "경기": "경기도", "충북": "충청북도", "충남": "충청남도",
            "전북": "전라북도", "제주": "제주도", "세종": "세종특별자치시",
            "서울": "서울특별시", "부산": "부산광역시", "대구": "대구광역시",
            "인천": "인천광역시", "광주": "광주광역시", "대전": "대전광역시", "울산": "울산광역시"
        }
        
        df["City"] = df.iloc[:, 1].astype(str).str.strip()
        df = df[df["City"] != "소계"]
        province_raw = df.iloc[:, 0].astype(str).str.strip()
        df["Province"] = province_raw.map(province_map).fillna(province_raw)
        
        df["FieldArea"] = df.iloc[:, 16].astype(str).str.replace(" ", "").str.replace(",", "").apply(pd.to_numeric, errors="coerce")
        
        return df[["Province", "City", "FieldArea"]].dropna()
    except Exception as e:
        return pd.DataFrame()

# ==========================================
# 3. [시각화] 1년간 지가 변동률 추세 (강조 색상 변경 적용)
# ==========================================
def draw_fluctuation_trend(file_path):
    print("\n" + "="*60)
    print("[시각화] 최근 1년 지가 변동률 추세 그래프 생성")
    print("="*60)

    if not check_file_exists(file_path):
        return

    try:
        try: df = pd.read_csv(file_path, encoding="cp949")
        except: df = pd.read_csv(file_path, encoding="utf-8")
        
        if "항목" in df.columns:
            df = df[df["항목"] == "지가변동률[%]"].copy()

        # 날짜 컬럼 추출 (24.09 ~ 25.09)
        date_cols = []
        date_mapping = {}
        pattern = re.compile(r'(\d{4})[\.\년/\-\s]+(\d{1,2})')

        for col in df.columns:
            match = pattern.search(str(col))
            if match:
                year, month = match.groups()
                date_int = int(year) * 100 + int(month)
                if 202409 <= date_int <= 202509:
                    date_cols.append(col)
                    date_mapping[col] = date_int

        if not date_cols:
            all_dates = []
            for col in df.columns:
                if pattern.search(str(col)): all_dates.append(col)
            if all_dates:
                date_cols = all_dates[-13:]
            else:
                return

        target_cols = sorted(date_cols, key=lambda x: date_mapping.get(x, 0))
        
        # 시도 추출
        city_col = [c for c in df.columns if "시군구" in c or "지역" in c][0]
        df['Province'] = df[city_col].apply(lambda x: x.split()[0] if isinstance(x, str) else "")
        df = df[~df['Province'].isin(["전국", "소계"])]
        
        for col in target_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        trend_df = df.groupby('Province')[target_cols].mean()
        
        # 그래프 그리기
        plt.figure(figsize=(14, 8))
        
        x_labels = []
        for c in target_cols:
            match = pattern.search(str(c))
            if match:
                y, m = match.groups()
                x_labels.append(f"{y[2:]}.{m.zfill(2)}")
            else:
                x_labels.append(c)
        
        # 비교군 설정 (파란색으로 강조할 지역들)
        # 데이터 원본이 '경북', '전남', '경남' 처럼 축약형일 수 있으므로 포함 여부 확인
        compare_group = ['경상북도', '전라남도', '경상남도', '경북', '전남', '경남']

        # 1. 배경 (그 외 지역) 그리기
        for province in trend_df.index:
            y_values = trend_df.loc[province]
            
            # 강원도와 비교군은 건너뜀 (나중에 그림)
            if "강원" in province: continue
            if province in compare_group: continue
            
            plt.plot(x_labels, y_values, color='lightgray', alpha=0.5, linewidth=1.5)

        # 2. 비교군 (경북, 전남, 경남) 그리기 - 파란색
        for province in trend_df.index:
            if province in compare_group:
                y_values = trend_df.loc[province]
                # 라벨에 이름 표시
                plt.plot(x_labels, y_values, color='royalblue', linewidth=2.5, alpha=0.8, label=province)
                
                # 마지막 값 텍스트 표시 (선택사항)
                plt.text(len(x_labels)-1, y_values.iloc[-1], f"{province}", 
                         ha='left', va='center', color='royalblue', fontsize=9, fontweight='bold')

        # 3. 주인공 (강원도) 그리기 - 빨간색
        if any("강원" in idx for idx in trend_df.index):
            gw_idx = [idx for idx in trend_df.index if "강원" in idx][0]
            gw_values = trend_df.loc[gw_idx]
            plt.plot(x_labels, gw_values, color='crimson', linewidth=4, marker='o', label=gw_idx, zorder=10)
            
            for i, val in enumerate(gw_values):
                plt.text(i, val + 0.005, f"{val:.2f}%", ha='center', va='bottom', 
                         color='crimson', fontweight='bold', fontsize=10)

        plt.title(f"시도별 지가 변동률 추이 비교 ({x_labels[0]} ~ {x_labels[-1]})", fontsize=16, fontweight='bold', pad=20)
        plt.ylabel("변동률 (%)", fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.legend(fontsize=11, loc='upper left')
        plt.tight_layout()
        plt.show()
        print(" -> 추세 그래프 생성 완료")

    except Exception as e:
        print(f" [Error] 추세 그래프 오류: {e}")

# ==========================================
# 4. 메인 실행 함수
# ==========================================
def main():
    f_latest = create_latest_csv()
    f_fluctuation = "시군구별용도지역별이용상황별 지가변동률.csv"
    f_area = "시군별_논밭별_경지면적_20251107103537.csv"

    # 1. 데이터 로드 및 병합
    df_latest = get_latest_data(f_latest)
    df_f = get_fluctuation_data(f_fluctuation)
    df_a = get_area_data(f_area)

    area_growth = pd.merge(df_a, df_f, on="City", how="left")
    prov_stats = area_growth.groupby("Province")[["FieldArea", "GrowthRate"]].mean().reset_index()
    final_df = pd.merge(df_latest, prov_stats, on="Province", how="left")
    final_df = final_df.sort_values("BasePrice", ascending=False)

    print("\n" + "="*60)
    print("[Result] 시도별 종합 데이터 집계 결과")
    print("="*60)
    print(final_df.to_string())

    # 2. 막대 그래프 생성 (지가변동률 제외)
    metrics = [
        ("BasePrice", "평균 농지가격 (원/㎡)", "2025년 2분기 실거래가 기준"),
        ("FieldArea", "평균 밭 경지면적 (ha)", "2025년 11월 기준"),
        ("Total_Volume", "총 거래 필지 수 (건)", "2025년 2분기 실거래 신고 기준")
    ]

    for col, title, period in metrics:
        fig, ax = plt.subplots(1, 1, figsize=(12, 7))
        sub_data = final_df[["Province", col]].dropna().sort_values(by=col, ascending=False)
        
        if sub_data.empty: continue

        colors = ["crimson" if "강원" in str(idx) else "lightgray" for idx in sub_data["Province"]]
        bars = ax.bar(sub_data["Province"], sub_data[col], color=colors, edgecolor='black', linewidth=0.5)
        
        ax.set_title(f"시도별 {title}\n({period})", fontsize=14, fontweight='bold', pad=20)
        ax.set_ylabel(title.split("(")[0].strip())
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        for bar, province, value in zip(bars, sub_data["Province"], sub_data[col]):
            color = 'red' if "강원" in str(province) else 'black'
            fontweight = 'bold' if "강원" in str(province) else 'normal'
            
            if col == "FieldArea": label = f"{value:,.1f}"
            else: label = f"{value:,.0f}"
            
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), label, 
                    ha='center', va='bottom', color=color, fontweight=fontweight, fontsize=9)
        
        plt.tight_layout()
        plt.show()

    # 3. 추세 그래프 생성 (수정된 함수)
    draw_fluctuation_trend(f_fluctuation)

if __name__ == "__main__":
    main()
