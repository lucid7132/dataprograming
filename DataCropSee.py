import pandas as pd

# 1. 데이터 로드 및 전처리
df = pd.read_csv('data/4도 과실 생산량.csv', encoding='cp949', header=[0, 1], thousands=',')

df.set_index(df.columns[0], inplace=True)
df.index.name = '시도'
df = df.stack(level=0)
df.index.names = ['시도', '연도']
df = df.reset_index()
df_melted = df.melt(id_vars=['시도', '연도'], var_name='상세정보', value_name='값')
split_data = df_melted['상세정보'].str.split(':', expand=True)
df_melted['작물'] = split_data[0]
df_melted['항목'] = split_data[1]
final_df = df_melted[['시도', '연도', '작물', '항목', '값']]

# ==========================================
# [핵심 수정] 데이터를 숫자로 깔끔하게 정리
# ==========================================
final_df['값'] = pd.to_numeric(final_df['값'], errors='coerce') # 문자를 숫자로, 안되면 NaN
final_df['값'] = final_df['값'].fillna(0) # NaN을 0으로

# 2. 범인(이상치) 찾기
# 값이 가장 큰 순서대로 상위 20개 출력
print("=== 값이 가장 큰 데이터 Top 20 ===")
top_values = final_df.sort_values(by='값', ascending=False).head(20)
print(top_values)

import matplotlib.pyplot as plt
import seaborn as sns

# 1. 폰트 및 마이너스 설정
plt.rc('font', family='Malgun Gothic')
plt.rc('axes', unicode_minus=False)

# 2. 데이터 준비
# - '합계'는 제외하고 개별 작물만 남김
# - '생산량 (톤)' 항목만 선택
target_item = '생산량 (톤)'
df_plot = final_df[
    (final_df['항목'] == target_item) & 
    (final_df['작물'] != '합계')
]

# 3. 4개의 그래프 틀 만들기 (2행 2열)
fig, axes = plt.subplots(2, 2, figsize=(20, 12))
axes = axes.flatten() # 4개의 칸을 1줄로 펴서 다루기 쉽게 만듦

# 지역 리스트 (데이터에 있는 시도 목록 가져오기)
regions = df_plot['시도'].unique()

# 4. 반복문으로 각 지역별 그래프 그리기
for i, region in enumerate(regions):
    # 해당 지역 데이터만 뽑기
    local_data = df_plot[df_plot['시도'] == region]
    
    # 그래프 그리기 (ax=axes[i] 옵션으로 i번째 칸에 그림)
    sns.lineplot(
        data=local_data, 
        x='연도', 
        y='값', 
        hue='작물', 
        marker='o', 
        linewidth=2,
        ax=axes[i]
    )
    
    # 각 그래프 꾸미기
    axes[i].set_title(f'{region} 작물별 생산량 변화', fontsize=16, fontweight='bold')
    axes[i].set_xlabel('연도')
    axes[i].set_ylabel('생산량 (톤)')
    axes[i].grid(True, linestyle='--', alpha=0.6)
    
    # 범례 위치 조정 (그래프 안쪽에 둬서 공간 활용)
    axes[i].legend(title='작물', loc='upper left')

# 5. 전체 레이아웃 다듬기
plt.tight_layout()
plt.show()