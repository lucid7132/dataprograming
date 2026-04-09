import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os


plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False


def load_gangwon_data(file_path):
    df = pd.read_csv(file_path, encoding='utf-8')
    stations = {
        '강원': ['속초', '철원', '춘천', '강릉', '원주', '대관령', '인제', '홍천', '태백'],


        '경남': ['창원', '통영', '거제', '밀양', '산청', '거창', '합천', '남해', '진주'],


        '경북': ['구미', '문경', '봉화', '안동', '영덕', '영주', '영천', '울진', '의성', '포항'],


        '전남': ['목포', '여수', '완도', '고흥', '해남', '장흥']
    }

    station_to_province = {}
    for province, station_list in stations.items():
        for station in station_list:
            station_to_province[station] = province
            
    all_stations = list(station_to_province.keys())
    
    df = df[df['지점명'].isin(all_stations)].copy()
    df['시도'] = df['지점명'].map(station_to_province)

    df['일시'] = pd.to_datetime(df['일시'])
    df['연도'] = df['일시'].dt.year
    df['월'] = df['일시'].dt.month
    
    cols = ['합계 일조시간(hr)']
    for c in cols:
        if c in df.columns: df[c] = df[c].fillna(0)
    return df

def aggregate_climate_stats(df):
    results = []
    for (station, province), group in df.groupby(['지점명', '시도']):
        winter_temp = group[group['월'].isin([12,1,2])]['최저기온(°C)'].mean()
        wind = group['평균풍속(m/s)'].mean()
        sun = group.groupby('연도')['합계 일조시간(hr)'].sum().mean()

        # SPI 지수는 -1.0 이하가 매우 건조, 1.5 이상이 매우 습윤으로 간주
        drought_count = len(group[(group['SPI3'] <= -1.0) | (group['SPI6'] <= -1.0)])

        # 전체 기간으로 나누어 '빈도(비율)' 계산
        drought = drought_count / len(group)
        wet = len(group[group['SPI3'] >= 1.5]) + len(group[group['SPI6'] >= 1.5])

        results.append({
            '지역': station,
            '시도' : province,
            '겨울기온': winter_temp,
            '평균풍속': wind,
            '일조시간': sun,
            '가뭄안전성' : drought,
            '침수안정성' : wet
        })
    return pd.DataFrame(results)

#  추천 점수 계산
def calculate_recommendation_score(df, weights):
    rec = df.copy()
    
    # 긍정 요인 정규화 (클수록 좋음 겨울기온, 일조시간)
    for col in ['겨울기온', '일조시간']:
        rec[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
        
    # 부정 요인 정규화 (작을수록 좋음 여름강수, 가뭄 침수 빈도)
    for col in ['가뭄안전성', '침수안정성']:
        if df[col].max() == df[col].min():
            rec[col] = 1.0
        else:
            rec[col] = 1 - ((df[col] - df[col].min()) / (df[col].max() - df[col].min()))
    
    
    # 풍속은 1~3m/s가 가장 적합
    # 10m/s는 사람이 살기 힘든 정도이므로 0점 처리
    # 1~3m/s는 만점(점수 1점)
    # 0~1m/s, 3~10m/s는 선형적으로 점수 감소
    def wind_speed_score(x):
        min = 1.0
        max = 3.0
        limit = 10.0
        if x < min:
            return x / min
        elif min <= x <= max:
            return 1.0
        else:
            if x >= limit:
                return 0.0
            else:
                return 1.0 - ((x - max) / (limit - max))
    
    rec['평균풍속'] = df['평균풍속'].apply(wind_speed_score)


    rec['추천점수'] = (
        rec['겨울기온'] * weights['겨울기온'] +
        rec['평균풍속'] * weights['평균풍속'] +
        rec['일조시간'] * weights['일조시간'] +
        rec['가뭄안전성'] * weights['가뭄안전성'] +
        rec['침수안정성'] * weights['침수안정성']
    )
    total_weight = sum(weights.values())
    rec['추천점수'] = (rec['추천점수'] / total_weight) * 100
    return rec.sort_values('추천점수', ascending=False)


def visualization(rec_df):
    # 그래프 1: 전체 순위 (Top 20)
    plt.figure(figsize=(14, 8))
    top_20 = rec_df.head(20)
    ax = sns.barplot(data=top_20, x='추천점수', y='지역', hue='시도', dodge=False)

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
    provinces = ['강원', '경남', '경북', '전남']
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()

    for i, province in enumerate(provinces):
        province_df = rec_df[rec_df['시도'] == province].head(5)
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
    file_name = 'merged_weather_spi.csv'
    
    if os.path.exists(file_name):
        df_raw = load_gangwon_data(file_name)
        df_stats = aggregate_climate_stats(df_raw)
        
        # 중요하다고 생각하는 요인의 가중치를 더 높게 줄수록 더 높은 점수를 부여함
        # 강원도의 기온이 타 지역보다 많이 낮으므로 기온에 더 가중치를 둠
        user_weights = {
            '겨울기온': 2.0,   # 중요함
            '일조시간': 1.5,   # 식물 성장에 필수
            '평균풍속': 1.5,   # 적당한 환기 필요
            '가뭄안전성': 2.0,   # 기온만큼 중요하게 설정
            '침수안정성': 2.0    # 기온만큼 중요하게 설정
        }
        rec_df = calculate_recommendation_score(df_stats, user_weights)
        
        print("추천 TOP 10")
        print(rec_df[['지역', '시도', '추천점수']].head(5))
        
        visualization(rec_df)
        
    else:
        print("파일을 찾을 수 없습니다.")