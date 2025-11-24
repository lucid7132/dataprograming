import pandas as pd
import matplotlib.pyplot as plt

# 연령별 귀농인구수를 막대 그래프로 시각화 하는 코드입니다 

path = "Processing_population/data/연령별_귀농가구원_2013_2024.csv"

# 그래프 폰트 (깨져서 설정)
plt.rc('font', family='Malgun Gothic')

# pandas 이용 csv읽기 
try:
    df = pd.read_csv(path, encoding="utf-8")
except:
    df = pd.read_csv(path, encoding="cp949")

# 의미없는 행 제거 
df.drop(index=df.index[0:2], axis=0, inplace=True)

# 지역을 열로 설정 
df.set_index("연령별", inplace=True)
df = df.drop(columns='성별')

# 열에 연령이 오도록 전치
df_trans = df.T

# 데이터숫자로 변환, 안하면 그래프가 겹쳐서 그려지지 않았습니다 
df_trans = df_trans.replace(',', '', regex=True).apply(pd.to_numeric)


# 막대 그래프 시각화
ax = df_trans.plot(kind='bar', figsize=(14, 8), width=0.8, colormap='Set2')

plt.title('연령별 귀농인구수')
plt.ylabel('인구 수')
plt.grid(axis='y', linestyle='--', linewidth=0.5)
plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), title="연령대")
plt.xticks(rotation=0)

plt.tight_layout()
plt.savefig("Processing_population/연령별 귀농인구수.png")
plt.show()
