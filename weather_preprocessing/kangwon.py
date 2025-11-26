# 4개 도(강원, 경남, 경북, 전남)의 기후 데이터를 분석하여 사용자 선호도(가중치)에 따른 귀농 최적지 순위를 산출하고 그래프로 시각화하는 코드
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import matplotlib.font_manager as fm


plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False


def load_weather_data(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except:
        try:
            df = pd.read_csv(file_path, encoding='cp949')
        except:
            df = pd.read_csv(file_path, encoding='euc-kr')

    # 도별 지점 정의
    stations = {
        '강원도': ['속초', '북춘천', '철원', '대관령', '춘천', '북강릉', '강릉', '동해', '원주', '영월', '인제', '홍천', '태백', '정선군'],
        '경상남도': ['창원', '진주', '통영', '거제', '밀양', '산청', '거창', '합천', '남해', '의령군', '함양군'],
        '경상북도': ['포항', '경주', '안동', '구미', '영주', '문경', '영덕', '울진', '울릉도', '상주', '봉화', '의성', '청송군'],
        '전라남도': ['목포', '여수', '순천', '완도', '진도', '고흥', '해남', '강진군', '장흥', '영광군', '흑산도']
    }
    
    # 지점명 -> 도 매핑 생성
    station_to_province = {}
    for province, station_list in stations.items():
        for station in station_list:
            station_to_province[station] = province
            
    all_stations = list(station_to_province.keys())
    
    df = df[df['지점명'].isin(all_stations)].copy()
    df['도'] = df['지점명'].map(station_to_province)
    
    df['일시'] = pd.to_datetime(df['일시'])
    df['연도'] = df['일시'].dt.year
    df['월'] = df['일시'].dt.month
    
    cols = ['월합강수량(00~24h만)(mm)', '최심적설(cm)', '합계 일조시간(hr)']
    for c in cols:
        if c in df.columns: df[c] = df[c].fillna(0)
    df = df[df['연도'] < 2023].copy()
    return df

def aggregate_climate_stats(df):
    results = []
    # 지점명과 도를 함께 그룹화
    for (station, province), group in df.groupby(['지점명', '도']):
        winter_temp = group[group['월'].isin([12,1,2])]['평균최저기온(°C)'].mean()
        summer_rain = group[group['월'].isin([6,7,8])].groupby('연도')['월합강수량(00~24h만)(mm)'].sum().mean()
        wind = group['평균풍속(m/s)'].mean()
        sun = group.groupby('연도')['합계 일조시간(hr)'].sum().mean()
        snow = group.groupby('연도')['최심적설(cm)'].max().mean()
        
        results.append({
            '지역': station,
            '도': province,
            '겨울기온': winter_temp,
            '여름강수': summer_rain,
            '평균풍속': wind,
            '일조시간': sun,
            '최대적설': snow
        })
    return pd.DataFrame(results)

#  추천 점수 계산
def calculate_recommendation_score(df, weights):
    rec = df.copy()
    
    # 긍정 요인 정규화 (클수록 좋음 겨울기온, 일조시간)
    for col in ['겨울기온', '일조시간']:
        rec[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
        
    # 부정 요인 정규화 (작을수록 좋음 여름강수, 평균풍속, 최대적설)
    for col in ['여름강수', '평균풍속', '최대적설']:
        rec[col] = 1 - ((df[col] - df[col].min()) / (df[col].max() - df[col].min()))
        
    rec['추천점수'] = (
        rec['겨울기온'] * weights['겨울기온'] +
        rec['여름강수'] * weights['여름강수'] +
        rec['평균풍속'] * weights['평균풍속'] +
        rec['일조시간'] * weights['일조시간'] +
        rec['최대적설'] * weights['최대적설']
    )
    total_weight = sum(weights.values())
    rec['추천점수'] = (rec['추천점수'] / total_weight) * 100
    return rec.sort_values('추천점수', ascending=False)


def visualization(rec_df):
    # 그래프 1: 전체 순위 (Top 20)
    plt.figure(figsize=(14, 8))
    top_20 = rec_df.head(20)
    ax = sns.barplot(data=top_20, x='추천점수', y='지역', hue='도', dodge=False)
    
    ax.set_title('4개 도(강원, 경남, 경북, 전남) 귀농 최적지 종합 추천 순위 (Top 20)', fontsize=18, fontweight='bold')
    ax.set_xlabel('적합도 점수 (100점 만점)', fontsize=12)
    ax.set_ylabel('지역', fontsize=12)
    ax.set_xlim(0, 100)
    ax.grid(axis='x', alpha=0.3)
    
    for i, v in enumerate(top_20['추천점수']):
        ax.text(v + 1, i, f"{v:.1f}", va='center', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.show()

    # 그래프 2: 도별 순위 (Top 5)
    provinces = ['강원도', '경상남도', '경상북도', '전라남도']
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()

    for i, province in enumerate(provinces):
        province_df = rec_df[rec_df['도'] == province].head(5)
        ax = axes[i]
        sns.barplot(data=province_df, x='추천점수', y='지역', palette='viridis', ax=ax)
        
        ax.set_title(f'{province} 귀농 최적지 Top 5', fontsize=15, fontweight='bold')
        ax.set_xlabel('적합도 점수', fontsize=10)
        ax.set_ylabel('지역', fontsize=10)
        ax.set_xlim(0, 100)
        ax.grid(axis='x', alpha=0.3)
        
        for j, v in enumerate(province_df['추천점수']):
            ax.text(v + 1, j, f"{v:.1f}", va='center', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    file_name = 'OBS_ASOS_MNH_20251119143018.csv'
    
    if os.path.exists(file_name):
        df_raw = load_weather_data(file_name)
        df_stats = aggregate_climate_stats(df_raw)
        
        # 중요하다고 생각하는 요인의 가중치를 더 높게 줄수록 더 높은 점수를 부여함
        user_weights = {
            '겨울기온': 2.0, '여름강수': 1.0, '평균풍속': 2.0,
            '일조시간': 3.0, '최대적설': 2.5
        }
        rec_df = calculate_recommendation_score(df_stats, user_weights)
        
        print("종합 추천 TOP 10")
        print(rec_df[['지역', '도', '추천점수']].head(10))
        
        visualization(rec_df)
        
    else:

        print("파일을 찾을 수 없습니다.")
