import pandas as pd
import matplotlib.pyplot as plt

# 1. 데이터 프레임 생성 (이미지의 데이터를 그대로 옮김)
data = {
    '연령별': ['0 - 39세', '40 - 49세', '50 - 59세', '60 - 69세', '70세 이상'],
    '성별': ['계', '계', '계', '계', '계'],
    '2013': [4834, 3177, 5624, 2841, 842],
    '2014': [4877, 3238, 5841, 3057, 963],
    '2015': [5108, 3246, 6572, 3846, 1088],
    '2016': [5307, 3132, 6750, 4239, 1131],
    '2017': [4788, 2948, 6402, 4408, 1084],
    '2018': [4233, 2613, 5729, 4199, 1082],
    '2019': [3413, 2167, 5377, 4185, 1039],
    '2020': [3699, 2210, 5403, 4925, 1210],
    '2021': [3842, 2295, 5890, 6299, 1450],
    '2022': [3009, 1895, 4888, 5747, 1367],
    '2023': [2449, 1448, 4034, 4655, 1094],
    '2024': [2056, 1176, 2959, 3696, 823]
}

df = pd.DataFrame(data)

# 2. 데이터 전처리
# '연령별'을 인덱스로 설정하고, 그래프에 불필요한 '성별' 컬럼 제거
df = df.set_index('연령별')
df = df.drop(columns=['성별'])

print(df)

# 3. 한글 폰트 설정 (환경에 맞게 주석 해제하여 사용)
# Windows 사용자의 경우:
plt.rc('font', family='Malgun Gothic')
# Mac 사용자의 경우:
# plt.rc('font', family='AppleGothic')
# Google Colab 등의 경우 별도 폰트 설치 필요

# 마이너스 기호 깨짐 방지
plt.rcParams['axes.unicode_minus'] = False

# 4. 시각화: 연도별 비교를 위해 행/열 전환(Transpose) 후 그리기
# 현재 df는 행(Row)이 연령, 열(Col)이 연도입니다.
# 연도를 X축으로 두는 것이 추이를 보기에 좋으므로 .T를 사용하여 전치합니다.
df_transposed = df.T 

# 그래프 그리기
ax = df_transposed.plot(kind='bar', figsize=(14, 8), width=0.8)

# 5. 그래프 스타일 꾸미기
plt.title('연도별 연령대 인구 추이 (2013-2024)', fontsize=16, pad=20)
plt.xlabel('연도', fontsize=12)
plt.ylabel('인구 수', fontsize=12)
plt.legend(title='연령대', bbox_to_anchor=(1.05, 1), loc='upper left') # 범례를 그래프 밖으로
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.xticks(rotation=0) # X축 라벨 회전 없음

# 6. 그래프 표시
plt.tight_layout()
plt.show()