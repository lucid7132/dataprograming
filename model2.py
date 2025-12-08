import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
import matplotlib.font_manager as fm
import os
import platform

# ==========================================
# 0. 한글 폰트 설정 (OS별 호환성 강화)
# ==========================================
def set_korean_font():
    system_name = platform.system()
    try:
        if system_name == 'Windows':
            font_path = 'C:/Windows/Fonts/malgun.ttf'
            if os.path.exists(font_path):
                font_name = fm.FontProperties(fname=font_path).get_name()
                plt.rc('font', family=font_name)
            else:
                plt.rc('font', family='Malgun Gothic')
        elif system_name == 'Darwin':  # Mac
            plt.rc('font', family='AppleGothic')
        else:  # Linux etc.
            plt.rc('font', family='NanumGothic')
            
        plt.rcParams['axes.unicode_minus'] = False 
        print(f"✅ 폰트 설정 완료: {plt.rcParams['font.family']}")
    except Exception as e:
        print(f"⚠️ 폰트 설정 오류: {e}")
        print("기본 폰트로 진행합니다.")

set_korean_font()

# ==========================================
# 1. 데이터 로드 및 전처리
# ==========================================
INPUT_FILENAME = "final_dataset_for_ai.csv" 

# (테스트용 더미 데이터 생성 코드 - 실제 파일이 없을 경우 작동)
if not os.path.exists(INPUT_FILENAME):
    print(f"⚠️ '{INPUT_FILENAME}' 파일이 없어 테스트용 더미 데이터를 생성합니다.")
    years = np.arange(2015, 2025) # 2015~2024
    regions = ['강원도', '경상남도', '경상북도', '전라남도']
    data = []
    for y in years:
        for r in regions:
            # 임의의 환경 변수 및 귀농 인구 생성
            temp = 12 + np.random.normal(0, 1) + (y-2015)*0.1
            infra = 50 + np.random.normal(0, 5) + (y-2015)*2
            pop = 1000 + (infra * 10) - (temp * 5) + np.random.normal(0, 50)
            if r == '강원도': pop += 500 # 강원도 프리미엄
            data.append([y, r, temp, infra, pop])
    df = pd.DataFrame(data, columns=['연도', '지역', '평균기온', '생활인프라지수', '귀농인구수'])
else:
    print(f"📂 '{INPUT_FILENAME}' 데이터를 불러옵니다...")
    df = pd.read_csv(INPUT_FILENAME)

# 데이터 정렬
df = df.sort_values(['지역', '연도'])

# 학습에 사용할 컬럼 선정
exclude_cols = ['귀농인구수', '연도', 'Unnamed: 0', '지역']
features = [c for c in df.columns if c not in exclude_cols]
cat_features = [c for c in features if df[c].dtype == 'object']
target = '귀농인구수'

print(f"🔍 학습 Feature 목록: {features}")

# ---------------------------------------------------------
# 데이터셋 분리
# ---------------------------------------------------------
# 2024년까지의 데이터를 학습 데이터로 사용
train_df = df[df['연도'] <= 2024].copy().dropna(subset=features)

X = train_df[features]
y = train_df[target]

# Train / Validation 분리 (8:2)
# 시계열 특성이 강하다면 shuffle=False가 좋으나, 환경 변수-인구 관계 학습이 목적이므로 shuffle=True 유지
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=True)

print(f"📊 데이터셋 현황: Train({len(X_train)}), Val({len(X_val)})")

# ==========================================
# 2. 모델 학습 (과적합 방지 파라미터 적용)
# ==========================================
print("\n🤖 모델 학습 시작 (CatBoost)...")

model = CatBoostRegressor(
    iterations=3000,
    learning_rate=0.04,       # 학습률을 0.03 -> 0.05로 소폭 상향
    depth=6,                  # 기존 4 -> 6 (모델이 더 복잡한 패턴을 학습하도록 깊이 증가)
    l2_leaf_reg=8,            # 기존 5 -> 3 (규제를 줄여서 데이터에 더 맞추도록 설정)
    loss_function='RMSE',
    eval_metric='RMSE',
    random_seed=42,
    verbose=100
)

model.fit(
    X_train, y_train,
    eval_set=(X_val, y_val),
    early_stopping_rounds=100, # 100번 동안 성능 향상 없으면 조기 종료
    cat_features=cat_features,
    use_best_model=True
)

best_score = model.get_best_score()['validation']['RMSE']
print(f"\n✅ 학습 완료. Best Validation RMSE: {best_score:.4f}")

# ==========================================
# 3. 2025년 예측
# ==========================================
target_regions = ['강원도', '경상남도', '경상북도', '전라남도']
pred_results = []

print("\n🔮 2025년 예측 수행 (가정: 2025년의 환경 변수는 2024년과 동일함)")

# 2024년 데이터(가장 최신 환경)를 입력값으로 사용
predict_input_df = df[df['연도'] == 2024].copy()

for region in target_regions:
    region_data = predict_input_df[predict_input_df['지역'] == region]
    
    if len(region_data) == 0:
        print(f"⚠️ {region}의 2024년 데이터가 없어 예측 불가")
        continue
        
    X_input = region_data[features]
    pred_val = model.predict(X_input)[0]
    
    pred_results.append({
        '연도': 2025,
        '지역': region,
        '귀농인구수': pred_val
    })

# 결과 병합
history_data = df[df['연도'] <= 2024][['연도', '지역', '귀농인구수']].copy()
pred_df = pd.DataFrame(pred_results)
full_data = pd.concat([history_data, pred_df], ignore_index=True).sort_values(['지역', '연도'])

# ==========================================
# 4. 시각화
# ==========================================
# 4-1. 시계열 그래프
plt.figure(figsize=(14, 7))
color_map = {'강원도': '#D32F2F', '경상남도': '#757575', '경상북도': '#9E9E9E', '전라남도': '#BDBDBD'}

for region in target_regions:
    subset = full_data[full_data['지역'] == region]
    if subset.empty: continue

    # 스타일 설정
    is_main = (region == '강원도')
    color = color_map.get(region, '#CCCCCC')
    lw = 4 if is_main else 2
    alpha = 1.0 if is_main else 0.6
    zorder = 10 if is_main else 1
    
    # 과거 데이터 및 예측 연결선
    plt.plot(subset['연도'], subset['귀농인구수'], 
             label=region, color=color, linewidth=lw, 
             alpha=alpha, zorder=zorder, marker='o', markersize=6)
    
    # 2025년 예측 지점 강조 (강원도)
    if is_main:
        val_2025 = subset[subset['연도'] == 2025]['귀농인구수'].values
        if len(val_2025) > 0:
            val = val_2025[0]
            plt.scatter(2025, val, color='red', s=300, marker='*', zorder=11, label='2025 예측(강원)')
            plt.text(2025, val + (val*0.05), f"{int(val):,}명", 
                     color='#D32F2F', fontweight='bold', ha='center', fontsize=14)

plt.title('지역별 귀농 인구 추이 및 2025년 예측', fontsize=18, fontweight='bold', pad=20)
plt.xlabel('연도', fontsize=12)
plt.ylabel('귀농 인구수 (명)', fontsize=12)
plt.xticks(np.arange(full_data['연도'].min(), 2026)) 
plt.grid(True, axis='y', linestyle='--', alpha=0.5)
plt.legend(fontsize=12, loc='upper left')
plt.tight_layout()
plt.show()

# 4-2. 변수 중요도 (Top 10)
importances = model.get_feature_importance()
if len(features) > 0:
    feature_imp = pd.Series(importances, index=X.columns).sort_values(ascending=False).head(10)

    plt.figure(figsize=(10, 6))
    sns.barplot(x=feature_imp.values, y=feature_imp.index, hue=feature_imp.index, palette='viridis', legend=False)
    plt.title('귀농 인구 결정 주요 요인 (Top 10)', fontsize=16, fontweight='bold')
    plt.xlabel('중요도 (Importance)')
    plt.tight_layout()
    plt.show()