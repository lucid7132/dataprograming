#강원도 3개 지역의 기후 데이터와 전국 상위 3개 지역의 평균값을 지표별로 비교하여 방사형 차트(Radar Chart)로 시각화하는 코드
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import matplotlib.font_manager as fm
import weather as wt
import kangwon as kw
from math import pi

plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False


def get_stats(df):
    results = []
    for (station, region), group in df.groupby(['지점명', '시도']):
        winter_temp = group[group['월'].isin([12,1,2])]['평균최저기온(°C)'].mean()
        summer_rain = group[group['월'].isin([6,7,8])].groupby('연도')['월합강수량(00~24h만)(mm)'].sum().mean()
        wind = group['평균풍속(m/s)'].mean()
        sun = group.groupby('연도')['합계 일조시간(hr)'].sum().mean()
        snow = group.groupby('연도')['최심적설(cm)'].max().mean()
        
        results.append({
            '지역': station,
            '시도': region,
            '겨울기온': winter_temp,
            '여름강수': summer_rain,
            '평균풍속': wind,
            '일조시간': sun,
            '최대적설': snow
        })
    return pd.DataFrame(results)


def select_comparison_groups(df, weights):
    # kangwon.py의 함수 이용
    rec = kw.calculate_recommendation_score(df, weights)
    
    # 강원도 Top 3
    gw_top3 = rec[rec['시도'] == '강원'].sort_values('추천점수', ascending=False).head(3).copy()
    gw_top3['구분'] = gw_top3['시도'] + ' ' + gw_top3['지역']
    
    # 강원 제외 전국 Top 3
    other_top3 = rec[rec['시도'] != '강원'].sort_values('추천점수', ascending=False).head(3)
    
    # 전국 Top 3 평균 계산
    other_mean = other_top3.mean(numeric_only=True).to_frame().T
    other_mean['지역'] = '전국 Top3 평균'
    other_mean['시도'] = '전국'
    other_mean['구분'] = '전국 Top3 평균'
    
    # 합치기 (강원 Top3 + 전국 Top3 평균)
    comparison_df = pd.concat([gw_top3, other_mean], ignore_index=True)
    
    return comparison_df


def plot_radar(df):
    # 시각화할 컬럼 정의 (기후요소만)
    categories = ['겨울기온', '여름강수', '평균풍속', '일조시간', '최대적설']
    N = len(categories)
    
    # 데이터 준비 (인덱스를 '구분'으로 설정)
    plot_data = df.set_index('구분')[categories]
    
    # 정규화 (0.2 ~ 1.0) - 0이 되는 것을 방지하여 시각적 왜곡 최소화
    # 공식: 0.2 + 0.8 * (x - min) / (max - min)
    norm_data = 0.2 + 0.8 * (plot_data - plot_data.min()) / (plot_data.max() - plot_data.min())
    
    # 방사형 차트 설정
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]  # 닫힌 도형을 만들기 위해 첫 번째 각도 추가
    
    plt.figure(figsize=(10, 10))
    ax = plt.subplot(111, polar=True)
    
    # 첫 번째 축이 12시 방향에 오도록 설정
    ax.set_theta_offset(pi / 2)
    ax.set_theta_direction(-1)
    
    # 축 라벨 설정
    plt.xticks(angles[:-1], categories, fontsize=12, fontweight='bold')
    
    # y축 라벨 설정 (0.2, 0.4, 0.6, 0.8)
    ax.set_rlabel_position(0)
    plt.yticks([0.2, 0.4, 0.6, 0.8], ["0.2", "0.4", "0.6", "0.8"], color="grey", size=10)
    plt.ylim(0, 1)
    
    # 각 지역별 데이터 플롯
    colors = ['#FF5733', '#33FF57', '#3357FF', '#FF33F6'] # 색상 지정
    
    for i, (idx, row) in enumerate(norm_data.iterrows()):
        values = row.values.flatten().tolist()
        values += values[:1]  # 닫힌 도형
        
        ax.plot(angles, values, linewidth=2, linestyle='solid', label=idx, color=colors[i % len(colors)])
        ax.fill(angles, values, color=colors[i % len(colors)], alpha=0.1)
    
    plt.title('강원 Top 3 vs 전국 Top 3(평균) 기후 특성 비교 (방사형 차트)', size=20, color='black', y=1.1, fontweight='bold')
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1), fontsize=12)
    
    plt.tight_layout()
    plt.show()


def main():
    file_name = 'OBS_ASOS_MNH_20251119143018.csv'
    
    if os.path.exists(file_name):

        # weather.py 에서 구현한 데이터 로드 및 전처리 함수 사용
        df_raw = wt.load_and_preprocess(file_name)

        df_stats = get_stats(df_raw)

        # 가중치 설정 (kangwon.py와 동일하게 설정하거나 사용자 정의)
        user_weights = {
            '겨울기온': 2.0, '여름강수': 1.0, '평균풍속': 2.0,
            '일조시간': 3.0, '최대적설': 2.5
        }
        
        # 비교 데이터 추출
        comparison_df = select_comparison_groups(df_stats, user_weights)

        print("비교 데이터 (Raw Values)")
        print(comparison_df[['구분', '겨울기온', '여름강수', '평균풍속', '일조시간', '최대적설']])
    
        plot_radar(comparison_df)
        
    else:

        print("파일을 찾을 수 없습니다.")

if __name__ == "__main__":
    main()
