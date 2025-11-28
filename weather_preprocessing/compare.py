import pandas as pd
import matplotlib.pyplot as plt
import os
import kangwon as kw
from math import pi

plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False




def select_comparison_groups(df, weights):
    # kangwon.py의 함수 이용
    rec = kw.calculate_recommendation_score(df, weights)
    
    # 강원도 Top 3
    gw_subset = rec[rec['시도'] == '강원'].copy()
    gw_top3 = gw_subset.sort_values('추천점수', ascending=False).head(3)
    
    gw_mean = gw_top3.mean(numeric_only=True).to_frame().T
    gw_mean['지역'] = '강원 Top3 평균'
    gw_mean['시도'] = '강원'
    gw_mean['구분'] = '강원 Top3 평균'
    
    # 강원 제외 전국 Top 3
    other_subset = rec[rec['시도'] != '강원'].copy()
    other_top3 = other_subset.sort_values('추천점수', ascending=False).head(3)
    
    # 전국 Top 3 평균 계산
    other_mean = other_top3.mean(numeric_only=True).to_frame().T
    other_mean['지역'] = '전국 Top3 평균'
    other_mean['시도'] = '전국'
    other_mean['구분'] = '전국 Top3 평균'
    
    # 합치기 (강원 Top3 + 전국 Top3 평균)
    comparison_df = pd.concat([gw_mean, other_mean], ignore_index=True)
    
    return comparison_df



def plot_radar(df):
    # 1. 시각화할 컬럼 지정
    categories = ['겨울기온', '가뭄안전성', '침수안정성', '평균풍속', '일조시간']
    N = len(categories)
    
    # 2. 각도 계산 (12시 방향 시작, 시계 방향)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]  # 닫힌 도형을 만들기 위해 첫 번째 각도 추가
    
    # 3. 그래프 초기화
    plt.figure(figsize=(10, 10))
    ax = plt.subplot(111, polar=True)
    
    # 시작 위치를 12시 방향으로, 방향을 시계 방향으로 설정
    ax.set_theta_offset(pi / 2)
    ax.set_theta_direction(-1)
    
    plt.xticks(angles[:-1], categories, fontsize=12, fontweight='bold')
    
    # 데이터가 0~1 범위이므로 0.2 단위로 눈금 표시
    ax.set_rlabel_position(0)
    plt.yticks([0.2, 0.4, 0.6, 0.8, 1.0], ["0.2", "0.4", "0.6", "0.8", "1.0"], color="grey", size=10)
    plt.ylim(0, 1.1) 
    
    # 색상: 강원(붉은색 계열), 전국(푸른색 계열)
    colors = ['#FF5733', '#3357FF'] 
    
    for i, row in df.iterrows():
        values = row[categories].tolist()
        values += values[:1]  # 마지막 점을 첫 번째 점과 연결하여 닫힌 도형 생성
        
        label_name = row['구분'] # 범례 이름
        
        # 선 그리기
        ax.plot(angles, values, linewidth=2, linestyle='solid', label=label_name, color=colors[i % len(colors)])
        # 면적 채우기
        ax.fill(angles, values, color=colors[i % len(colors)], alpha=0.1)
    
    # 7. 제목 및 범례 설정
    plt.title('강원 Top 3 vs 전국 Top 3 기후 요소 비교', size=20, color='black', y=1.1, fontweight='bold')
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1), fontsize=12)
    
    plt.tight_layout()
    plt.show()



if __name__ == "__main__":
    file_name = 'merged_weather_spi.csv'
    
    if os.path.exists(file_name):

        # weather.py 에서 구현한 데이터 로드 및 전처리 함수 사용
        df_raw = pd.read_csv(file_name, encoding='utf-8')

        df_stats = kw.aggregate_climate_stats(df_raw)

        # 가중치 설정
        user_weights = {
            '겨울기온': 2.0,   # 중요함
            '일조시간': 1.5,   # 식물 성장에 필수
            '평균풍속': 1.5,   # 적당한 환기 필요
            '가뭄안전성': 2.0,   # 기온만큼 중요하게 설정
            '침수안정성': 2.0    # 기온만큼 중요하게 설정
        }
        
        # 원주 포함하여 추출
        gw_selected = select_comparison_groups(df_stats, user_weights)

        print("비교 데이터 (Raw Values)")
        print(gw_selected[['구분', '겨울기온', '가뭄안전성', '침수안정성', '평균풍속', '일조시간']])

        
    
        plot_radar(gw_selected)
        
    else:
        print("파일을 찾을 수 없습니다.")