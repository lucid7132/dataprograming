import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# 한글 폰트 설정 (Windows: Malgun Gothic, Mac: AppleGothic 등)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def get_price_data(file_path):
    print(f"[1/5] 기준 땅값 데이터 로드 중... ({file_path})")
    try:
        try:
            df = pd.read_csv(file_path, header=None, skiprows=3, encoding="cp949")
        except:
            df = pd.read_csv(file_path, header=None, skiprows=3, encoding="utf-8")

        if df.empty: return pd.DataFrame(columns=["Province", "City", "BasePrice"])
        df = df[df[0].notna()].copy()

        def split_region(addr):
            addr = str(addr).strip()
            tokens = addr.split()
            if len(tokens) <= 1: return tokens[0] if tokens else None, tokens[0] if tokens else None
            return tokens[0], tokens[-1]

        df[["Province", "City"]] = df[0].apply(lambda x: pd.Series(split_region(x)))
        df = df.dropna(subset=["City"])
        
        # 9번 컬럼: 평균지가
        df["BasePrice"] = df[9].astype(str).str.replace(",", "", regex=False).apply(pd.to_numeric, errors="coerce")
        return df[["Province", "City", "BasePrice"]].dropna()
    except Exception as e:
        print(f"   [Error] 땅값 파일 읽기 실패: {e}")
        return pd.DataFrame(columns=["Province", "City", "BasePrice"])

def get_fluctuation_data(file_path):
    print(f"[2/5] 지가 변동률 데이터 로드 중... ({file_path})")
    try:
        try:
            df = pd.read_csv(file_path, encoding="cp949")
        except:
            df = pd.read_csv(file_path, encoding="utf-8")

        df = df[df["항목"] == "지가변동률[%]"].copy()
        month_cols = [c for c in df.columns if "월" in str(c)]
        if not month_cols: return pd.DataFrame(columns=["City", "GrowthRate"])

        # 날짜 parsing 하여 가장 최근 월 찾기
        def parse_date(c):
            digits = "".join(filter(str.isdigit, c))
            return int(digits) if digits else 0
        
        recent_col = sorted(month_cols, key=parse_date)[-1]
        
        df["City"] = df["시군구별"].astype(str).str.strip()
        # '전국', '~~도' 제외
        df = df[~df["City"].isin(["전국"]) & ~df["City"].str.endswith("도")]

        df["GrowthRate"] = pd.to_numeric(df[recent_col], errors="coerce")
        
        # 도시별 평균 (같은 시군구 이름이 있을 수 있으므로 grouping)
        return df.groupby("City", as_index=False)["GrowthRate"].mean()
    except Exception as e:
        print(f"에러 지가 변동률 파일 읽기 실패: {e}")
        return pd.DataFrame(columns=["City", "GrowthRate"])

def get_area_data(file_path):
    print(f"[3/5] 경지(밭) 면적 데이터 로드 중... ({file_path})")
    try:
        try:
            df = pd.read_csv(file_path, encoding="cp949")
        except:
            df = pd.read_csv(file_path, encoding="utf-8")

        df = df[2:].reset_index(drop=True)
        df.columns = [f"Column{i+1}" for i in range(df.shape[1])]

        province_map = {"강원": "강원도", "전남": "전라남도", "경북": "경상북도", "경남": "경상남도"}

        df["City"] = df["Column2"].astype(str).str.strip()
        df = df[df["City"] != "소계"]
        df["Province"] = df["Column1"].astype(str).str.strip().map(province_map)
        df["FieldArea"] = df["Column17"].astype(str).str.replace(" ", "").str.replace(",", "").apply(pd.to_numeric, errors="coerce")

        return df[["Province", "City", "FieldArea"]].dropna()
    except Exception as e:
        print(f"    에러 경지면적 파일 읽기 실패: {e}")
        return pd.DataFrame(columns=["Province", "City", "FieldArea"])

def get_combined_volume_data(f_status, f_trend):
    print(f"[4,5/5] 거래량 데이터 통합 로드 중...")
    dfs = []
    
    # 1. 거래현황 파일
    try:
        try: df = pd.read_csv(f_status, encoding="cp949")
        except: df = pd.read_csv(f_status, encoding="utf-8")
        if "Column4" in df.columns:
            df["Region"] = df["Column4"].astype(str).str.strip()
            def split(x):
                t = x.split()
                return (t[0], t[-1]) if len(t)>=2 else (None, None)
            df[["Province", "City"]] = df["Region"].apply(lambda x: pd.Series(split(x)))
            df["Vol"] = df["Column5"].astype(str).str.replace(",", "").replace("-", "0").apply(pd.to_numeric, errors="coerce")
            dfs.append(df[["Province", "City", "Vol"]])
    except Exception as e: print(f"   [Warning] 현황 파일 로드 에러: {e}")

    # 2. 동향분석 파일
    try:
        try: df = pd.read_csv(f_trend, encoding="cp949")
        except: df = pd.read_csv(f_trend, encoding="utf-8")
        if "AREANM" in df.columns:
            df["Region"] = df["AREANM"].astype(str).str.strip()
            def split(x):
                t = x.split()
                return (t[0], t[-1]) if len(t)>=2 else (None, None)
            df[["Province", "City"]] = df["Region"].apply(lambda x: pd.Series(split(x)))
            df["Vol"] = df["LNDPCL"].astype(str).str.replace(",", "").apply(pd.to_numeric, errors="coerce")
            dfs.append(df[["Province", "City", "Vol"]])
    except Exception as e: print(f"   [Warning] 동향 파일 로드 에러: {e}")

    if not dfs: return pd.DataFrame(columns=["Province", "City", "Total_Volume"])
    
    full = pd.concat(dfs)
    # 시군구별 합계
    return full.groupby(["Province", "City"], as_index=False)["Vol"].sum().rename(columns={"Vol": "Total_Volume"}) 
    
def main():
    # 파일명 정의 (실제 파일 경로 확인 필요)
    f_price = "2014년+1분기+시.군별+필지별+평균가격+현황.csv"
    f_fluctuation = "시군구별용도지역별이용상황별 지가변동률.csv"
    f_area = "시군별_논밭별_경지면적_20251107103537.csv"
    f_status = "농지시군별거래현황.csv"
    f_trend = "농지+실거래가+동향분석결과.csv"

    # 1. 데이터 로드
    df_p = get_price_data(f_price)
    df_f = get_fluctuation_data(f_fluctuation)
    df_a = get_area_data(f_area)
    df_v = get_combined_volume_data(f_status, f_trend)

    # 2. 데이터 병합 (Province, City 기준)
    merged = pd.merge(df_p, df_a, on=["Province", "City"], how="outer")
    merged = pd.merge(merged, df_v, on=["Province", "City"], how="outer")
    merged = pd.merge(merged, df_f, on="City", how="left")

    # 3. 데이터 정제 (Province 단위 집계를 위해)
    merged = merged.dropna(subset=["Province"])
    merged = merged[~merged["Province"].astype(str).str.contains("전국|소계|합계")]
    merged = merged[merged["Province"].astype(str).str.len() > 1]

    # 4. 시도(Province) 별 평균 계산
    numeric_cols = ["BasePrice", "GrowthRate", "FieldArea", "Total_Volume"]
    prov_avg = merged.groupby("Province")[numeric_cols].mean()
    prov_avg = prov_avg.sort_values("BasePrice", ascending=False)

    print("\n[Result] 시도별 지표 평균 산출 완료")
    print(prov_avg)

    # 5. 시각화 (개별 그래프로 출력)
    metrics = [
        ("BasePrice", "평균 농지가격 (원/㎡)"),
        ("GrowthRate", "평균 지가 변동률 (%)"),
        ("FieldArea", "평균 밭 경지면적 (ha)"),
        ("Total_Volume", "평균 거래량 (건)")
    ]

    for col, title in metrics:
        # ** 핵심 변경: 각 지표마다 1x1의 Figure를 새로 생성한다. **
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        # 해당 지표 데이터 추출 및 정렬
        sub_data = prov_avg[col].dropna().sort_values(ascending=False)
        
        if sub_data.empty:
            ax.text(0.5, 0.5, "데이터 없음", ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f"시도별 {title}")
            plt.tight_layout()
            plt.show()
            continue

        # 색상 설정 및 플롯 로직 (기존과 동일)
        colors = []
        for idx in sub_data.index:
            if "강원" in str(idx):
                colors.append("crimson")
            else:
                colors.append("lightgray")
        
        bars = ax.bar(sub_data.index, sub_data.values, color=colors)
        ax.set_title(f"시도별 {title}")
        ax.tick_params(axis='x', rotation=45)
        
        # 강원도 값 텍스트 표시
        for bar, idx in zip(bars, sub_data.index):
            if "강원" in str(idx):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height, 
                        f"{height:,.1f}", 
                        ha='center', va='bottom', color='red', fontweight='bold')

        plt.tight_layout()
        plt.show() # ** 핵심 변경: 그래프를 그릴 때마다 바로바로 띄운다. **

    print("완료: 4개의 개별 그래프가 순차적으로 생성되었습니다.")

if __name__ == "__main__":
    main()
