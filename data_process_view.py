import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import numpy as np
import os


START_YEAR = 2015   # 시작 연도
END_YEAR = 2024    # 종료 연도 (예측 포함 시 2025, 실측만 볼 경우 2024)

INPUT_FILENAME = "final_dataset.csv"


plt.style.use('seaborn-v0_8-white')

font_path = 'C:/Windows/Fonts/malgun.ttf'
try:
    font_name = fm.FontProperties(fname=font_path).get_name()
    plt.rc('font', family=font_name)
    plt.rc('axes', unicode_minus=False)
    print(f"폰트 설정 완료: {font_name}")
except:
    print("폰트 설정 실패. 기본 폰트로 진행합니다.")


if os.path.exists(INPUT_FILENAME):
    print(f"'{INPUT_FILENAME}' 파일을 불러옵니다.")
    df = pd.read_csv(INPUT_FILENAME)
else:
    print(f"파일이 없어 테스트 데이터를 생성합니다.")
    # 테스트 데이터 생성 시에도 설정한 연도 범위 사용
    years = np.arange(START_YEAR, END_YEAR + 1)
    regions = ['강원도', '경상남도', '경상북도', '전라남도']
    data_list = []
    
    for r in regions:
        base_pop = 1000 + np.random.randint(0, 500)
        for y in years:
            data_list.append({
                '연도': y,
                '지역': r,
                '귀농인구수': base_pop + np.random.randint(-200, 300),
                '평균지가': 10000 + (y - 2015) * 500 + np.random.randint(-500, 500),
                '평균기온': 12 + np.random.uniform(-1, 1),
                '강수량': 1200 + np.random.randint(-300, 300)
            })
    df = pd.DataFrame(data_list)

# 설정한 연도 범위로 데이터 필터링
df = df[(df['연도'] >= START_YEAR) & (df['연도'] <= END_YEAR)]

print(f"데이터 분석 기간: {START_YEAR}년 ~ {END_YEAR}년")


target_regions = ['강원도', '경상남도', '경상북도', '전라남도']
variables = [
    ('평균지가', '평균 지가 (원/㎡)', '#D32F2F'),  # 빨강
    ('평균기온', '평균 기온 (℃)', '#F57C00'),       # 주황
    ('강수량', '강수량 (mm)', '#1976D2')            # 파랑
]

# 전체 캔버스 크기 설정
fig, axes = plt.subplots(3, 4, figsize=(24, 16))


def draw_subplot(ax, df_sub, x_col, y1_col, y2_col, y2_label, color, is_first_col):

    # 1. 막대 그래프 (귀농 인구)
    sns.barplot(x=x_col, y=y1_col, data=df_sub, ax=ax, color='lightgray', alpha=0.6, zorder=1)
    
    if is_first_col: # 맨 왼쪽 열에만 y축 라벨 표시 
        ax.set_ylabel('귀농 인구수 (명)', fontsize=11, fontweight='bold', color='gray')
    else:
        ax.set_ylabel('') 
        
    ax.set_ylim(0, df_sub[y1_col].max() * 1.3)
    ax.grid(False)
    ax.set_xlabel('') # x축 라벨(연도)은 공간상 생략 또는 맨 아래만 표시

    # 2. 꺾은선 그래프 (환경 변수)
    ax2 = ax.twinx()
    sns.lineplot(x=ax.get_xticks(), y=df_sub[y2_col], ax=ax2, 
                 color=color, marker='o', linewidth=2, zorder=2)
    
    ax2.set_ylabel(y2_label, fontsize=11, fontweight='bold', color=color)
    ax2.tick_params(axis='y', colors=color)
    ax2.grid(True, axis='y', linestyle='--', alpha=0.3, color=color)

    return ax2 # 범례 처리를 위해 반환


for col_idx, region in enumerate(target_regions):
    # 해당 지역 데이터 필터링 및 연도별 평균 집계
    region_df = df[df['지역'] == region].copy()
    region_trend = region_df.groupby('연도')[['귀농인구수', '평균지가', '평균기온', '강수량']].mean().reset_index()

    for row_idx, (var_col, var_label, color) in enumerate(variables):
        ax = axes[row_idx, col_idx]

        draw_subplot(ax, region_trend, '연도', '귀농인구수', var_col, var_label, color, col_idx == 0)
        

        if row_idx == 0:
            ax.set_title(region, fontsize=18, fontweight='bold', pad=20, backgroundcolor='#f0f0f0')

plt.tight_layout()


save_filename = "all_regions_analysis_dashboard.png"
plt.savefig(save_filename, dpi=200, bbox_inches='tight')

print(f"\n 4개 지역 통합 분석 결과가 '{save_filename}'에 저장되었습니다.")
plt.show()