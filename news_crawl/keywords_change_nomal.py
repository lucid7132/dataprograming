import pandas as pd
import matplotlib.pyplot as plt
import os

# 폰트설정
plt.rc('font', family='Malgun Gothic') 
plt.rcParams['axes.unicode_minus'] = False

def keywords_change_by_year_normalized(df: pd.DataFrame):
    
    save_dir = "news_crawl/keywords_change_by_year"
    os.makedirs(save_dir, exist_ok=True)
    
    # 데이터 정규화 ( 0~1 로 변경)
    min_vals = df.min(axis=1)
    max_vals = df.max(axis=1)
    
    df_norm = (df.sub(min_vals, axis=0)).div(max_vals - min_vals, axis=0)
    df_norm = df_norm.drop(columns=['2020'])

    # 시각화를 위해 전치
    df_norm_T = df_norm.T
    
    # 꺾은선 그래프
    ax = df_norm_T.plot(kind='line', marker='o', figsize=(12, 6), colormap='Set2', linewidth=2)

    plt.title('연도별 키워드 변화 추이', fontsize=15)
    plt.ylabel('상대적 강도')
    plt.xticks(rotation=0)
    
    plt.legend(title='키워드', loc='center left', bbox_to_anchor=(1.02, 0.5))
    plt.tight_layout()
    
    save_path = f"{save_dir}/keywords_trend_normalized.png"
    plt.savefig(save_path)
    print(f"그래프가 저장되었습니다: {save_path}")
    plt.show()

if __name__ == "__main__":
    csv_file = "news_crawl/keywords_change_by_year/keywords_change_by_year.csv"
    
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file, index_col=0)
        df.columns = df.columns.astype(str) 
        
        keywords_change_by_year_normalized(df)
    else:
        print(f"{csv_file} 파일을 찾을 수 없습니다.")