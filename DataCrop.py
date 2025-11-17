import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. 데이터 불러오기
# header=[0, 1]: 2줄 헤더 인식, thousands=',': 숫자 쉼표 제거
df = pd.read_csv('data/4도 과실 생산량.csv', encoding='cp949', header=[0, 1], thousands=',')

# 2. 인덱스 정리
df.set_index(df.columns[0], inplace=True)
df.index.name = '시도'

# 3. 구조 변경 (Stack & Reset)
df = df.stack(level=0)           # 연도를 행으로 내림
df.index.names = ['시도', '연도'] # 인덱스 이름 설정
df = df.reset_index()            # 인덱스를 일반 컬럼으로 변환

# 4. 데이터 녹이기 (Melt)
df_melted = df.melt(id_vars=['시도', '연도'], var_name='상세정보', value_name='값')

# 5. 텍스트 분리 (Split)
split_data = df_melted['상세정보'].str.split(':', expand=True)
df_melted['작물'] = split_data[0]
df_melted['항목'] = split_data[1]

# 6. 최종 컬럼 정리
final_df = df_melted[['시도', '연도', '작물', '항목', '값']]

# ---------------------------------------------------------
# [추가된 부분] 7. CSV 파일로 내보내기
# ---------------------------------------------------------
# index=False: 불필요한 행 번호(0, 1, 2...) 저장 안 함
# encoding='cp949': 엑셀에서 한글 안 깨지게 저장 (맥/리눅스 위주면 'utf-8-sig' 추천)
final_df.to_csv('data/4도_과실_생산량_전처리완료.csv', index=False, encoding='cp949')

print("저장이 완료되었습니다: data/4도_과실_생산량_전처리완료.csv")
print(final_df.head()) # 저장된 데이터 미리보기


# 1. 한글 폰트 설정 (Windows 환경 기준)
# 맥(Mac) 사용자라면 'AppleGothic'으로 바꿔주세요.
plt.rc('font', family='Malgun Gothic')
plt.rc('axes', unicode_minus=False) # 마이너스 기호 깨짐 방지

# 2. 데이터 필터링
# 우리가 보고 싶은 항목: '생산량 (톤)'
# 제외할 작물: '합계' (전체 합계가 섞이면 개별 작물 변화가 잘 안 보임)
target_item = '생산량 (톤)'
df_plot = final_df[
    (final_df['항목'] == target_item) & 
    (final_df['작물'] != '합계')
]

# 3. 시도별 데이터를 합쳐서 '전국(4도 전체) 연도별 작물 생산량' 구하기
# 시도 구분 없이 연도와 작물로만 묶어서 값을 더합니다.
df_grouped = df_plot.groupby(['연도', '작물'])['값'].sum().reset_index()

# 4. 그래프 그리기
plt.figure(figsize=(12, 6)) # 그래프 크기 조절 (가로, 세로)

# seaborn의 lineplot 사용 (hue='작물' 옵션으로 작물별 색깔 다르게)
sns.lineplot(data=df_grouped, x='연도', y='값', hue='작물', marker='o', linewidth=2)

# 그래프 꾸미기
plt.title(f'연도별 작물 {target_item} 변화 추이', fontsize=16)
plt.xlabel('연도')
plt.ylabel(target_item)
plt.grid(True, linestyle='--', alpha=0.6) # 격자 무늬 추가
plt.legend(title='작물', bbox_to_anchor=(1.05, 1), loc='upper left') # 범례 밖으로 빼기

plt.tight_layout() # 여백 자동 조정
plt.show()