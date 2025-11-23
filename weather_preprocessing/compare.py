#강원도 3개 지역의 기후 데이터와 전국 상위 3개 지역의 평균값을 지표별로 비교하여 막대 그래프로 시각화하는 코드
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import matplotlib.font_manager as fm
import weather as wt
import kangwon as kw

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
    
    # 동해, 강릉, 원주
    target_gw = ['동해', '강릉', '원주']
    gw_selected = rec[rec['지역'].isin(target_gw)].copy()
    
    # 강원을 제외한 점수 상위 3지역
    top3_candidates = rec[rec['시도'] != '강원'].sort_values('추천점수', ascending=False).head(3)
    
    # 상위 3개의 데이터 평균
    top3_mean_series = top3_candidates.mean(numeric_only=True)
    other_top3 = top3_mean_series.to_frame().T
    
    
    other_top3['지역'] = '전국 Top3 평균'
    other_top3['시도'] = '전국'

    return gw_selected, other_top3



def plot_comparison(gw_df, other_df):
    comparison_df = pd.concat([gw_df, other_df])
    
    
    group_name = '강원'
    comparison_df['그룹'] = comparison_df['시도'].apply(lambda x: group_name if x == '강원' else '전국 기후 TOP3')
    
    metrics = [
        ('겨울기온', '겨울철 최저기온 (°C)'),
        ('여름강수', '여름철 총 강수량 (mm)'),
        ('평균풍속', '연평균 풍속 (m/s)'),
        ('일조시간', '연간 일조시간 (hr)'),
        ('최대적설', '연간 최대 적설 (cm)')
    ]
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    # 색상 설정
    palette = {group_name: 'blue', '전국 기후 TOP3': 'gray'}
    
    for i, (col, title) in enumerate(metrics):
        ax = axes[i]
        sns.barplot(data=comparison_df, x='지역', y=col, hue='그룹', dodge=False, ax=ax, palette=palette)
        
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel('')
        ax.legend_.remove()
        ax.grid(axis='y', alpha=0.3)
    
    

    handles, labels = axes[0].get_legend_handles_labels()
    axes[5].legend(handles, labels, title='비교 그룹', fontsize=14, loc='center')
    axes[5].axis('off')
    
    plt.suptitle('강원도 추천 3사(동해/강릉/원주) vs 전국 귀농 최적지 기후 비교', fontsize=20, fontweight='bold')
    plt.tight_layout()
    plt.show()



if __name__ == "__main__":
    file_name = 'OBS_ASOS_MNH_20251119143018.csv'
    
    if os.path.exists(file_name):

        # weather.py 에서 구현한 데이터 로드 및 전처리 함수 사용
        df_raw = wt.load_and_preprocess(file_name)

        df_stats = get_stats(df_raw)

        # 가중치 설정
        user_weights = {'겨울기온': 3.0, '여름강수': 1.0, '평균풍속': 2.0, '일조시간': 1.5, '최대적설': 2.5}
        
        # 원주 포함하여 추출
        gw_selected, other_top3 = select_comparison_groups(df_stats, user_weights)

        print("강원도 비교군 (원주 포함)")
        print(gw_selected[['지역', '추천점수', '겨울기온', '최대적설']])
    
        print("\n 전국 기후 최적지 TOP 3 (평균값)")
        print(other_top3[['지역', '추천점수', '겨울기온', '최대적설']])
    
        plot_comparison(gw_selected, other_top3)
        
    else:

        print("파일을 찾을 수 없습니다.")
