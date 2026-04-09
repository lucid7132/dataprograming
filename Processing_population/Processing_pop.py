import pandas as pd
import matplotlib.pyplot as plt

# 시도별 귀농인구수를 꺾은선 그래프로 시각화 하는 코드입니다 
# 평균을 통해 너무 적은 지역은 제외했습니다 

path = "Processing_population/data/시도별_귀농가구원수_2013_2024.csv"

# 그래프 폰트 (깨져서 설정)
plt.rc('font', family='Malgun Gothic')

# pandas 이용 csv읽기 
try:
    df = pd.read_csv(path, encoding="utf-8")
except:
    df = pd.read_csv(path, encoding="cp949")

# 의미없는 행 제거 
df.drop(index=df.index[0:3], axis=0, inplace=True)

# 지역을 열로 설정 
df.set_index("행정구역별", inplace=True)


# 연도가 있는 리스트 추출 ( 숫자로 변환 가능한 것만 )
year_list = [col for col in df.columns if col.isdigit()]
year_list = sorted(year_list)

# 열에 지역이 오도록 전치
df_trans = df[year_list].T

# 데이터숫자로 변환, 안하면 그래프가 겹쳐서 그려지지 않았습니다 
df_trans = df_trans.replace(',', '', regex=True).apply(pd.to_numeric)

# 상위 3지역 + 강원특별자치도만 남게 정리 
region_mean = df_trans.mean(axis=0)
region_mean = region_mean.sort_values()

target_regions = region_mean.index[-3:].tolist()
spec_region = '강원특별자치도'
if spec_region in df_trans.columns:
    if spec_region not in target_regions:
        target_regions.append(spec_region)
else:
    print(f"{spec_region} : 데이터가 없습니다.")

df_filtered = df_trans[target_regions]

# 꺾은선 그래프 시각화
plt.figure(figsize=(12, 7))

# 강원도 강조 
for region in df_filtered.columns:
    if region == '강원특별자치도':
        plt.plot(year_list, df_filtered[region], marker='o', linewidth=2, color='red', label=region)
    else:
        plt.plot(year_list, df_filtered[region], marker='o', linewidth=1.5, label=region)

plt.title('시도별 귀농인구수')
plt.xlabel('연도')
plt.ylabel('귀농인구수 (명)')
plt.grid(True, linestyle='--', linewidth=0.5)
plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), title="지역")
plt.tight_layout()
plt.savefig("Processing_population/시도별 귀농인구수.png")
#plt.show()