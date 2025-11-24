#강원도 주요 지역의 기후 데이터를 분석하여 사용자 선호도(가중치)에 따른 귀농 최적지 순위를 산출하고 그래프로 시각화하는 코드
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import matplotlib.font_manager as fm


plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False


def load_gangwon_data(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except:
        try:
            df = pd.read_csv(file_path, encoding='cp949')
        except:
            df = pd.read_csv(file_path, encoding='euc-kr')

    gangwon_stations = [
        '속초', '북춘천', '철원', '대관령', '춘천', '북강릉', '강릉', 
        '동해', '원주', '영월', '인제', '홍천', '태백', '정선군'
    ]
    df = df[df['지점명'].isin(gangwon_stations)].copy()
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
    for station, group in df.groupby('지점명'):
        winter_temp = group[group['월'].isin([12,1,2])]['평균최저기온(°C)'].mean()
        summer_rain = group[group['월'].isin([6,7,8])].groupby('연도')['월합강수량(00~24h만)(mm)'].sum().mean()
        wind = group['평균풍속(m/s)'].mean()
        sun = group.groupby('연도')['합계 일조시간(hr)'].sum().mean()
        snow = group.groupby('연도')['최심적설(cm)'].max().mean()
        
        results.append({
            '지역': station,
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
    
    plt.figure(figsize=(12, 8))


    ax = sns.barplot(data=rec_df, x='추천점수', y='지역', palette='viridis')
    
    ax.set_title('🟢 강원도 귀농 최적지 추천 순위 (높을수록 좋음)', fontsize=18, fontweight='bold')
    ax.set_xlabel('적합도 점수 (100점 만점)', fontsize=12)
    ax.set_ylabel('지역', fontsize=12)
    ax.set_xlim(0, 100)
    ax.grid(axis='x', alpha=0.3)
    
    for i, v in enumerate(rec_df['추천점수']):
        ax.text(v + 1, i, f"{v:.1f}", va='center', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.show()




if __name__ == "__main__":
    file_name = 'OBS_ASOS_MNH_20251119143018.csv'
    
    if os.path.exists(file_name):
        df_raw = load_gangwon_data(file_name)
        df_stats = aggregate_climate_stats(df_raw)
        
        # 중요하다고 생각하는 요인의 가중치를 더 높게 줄수록 더 높은 점수를 부여함
        # 강원도의 기온이 타 지역보다 많이 낮으므로 기온에 더 가중치를 둠
        user_weights = {
            '겨울기온': 3.0, '여름강수': 1.0, '평균풍속': 2.0,
            '일조시간': 1.5, '최대적설': 2.5
        }
        rec_df = calculate_recommendation_score(df_stats, user_weights)
        
        print("추천 TOP 5")
        print(rec_df[['지역', '추천점수']].head(5))
        
        visualization(rec_df)
        
    else:

        print("파일을 찾을 수 없습니다.")
