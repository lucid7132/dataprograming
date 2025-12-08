import pandas as pd
import matplotlib.pyplot as plt
import os

plt.rc('font', family='Malgun Gothic')


def keywords_change_by_year(df:pd):

    save_dir = "news_crawl/keywords_change_by_year"
    os.makedirs(save_dir, exist_ok=True)
    save_dir_file = f"{save_dir}/keywords_change_by_year"

    # 변화율 계산, 열을 기준으로 퍼신트단위로 변환합니다
    grow_rate = df.pct_change(axis=1) * 100
    grow_rate = grow_rate.drop(columns=['2020'])

    plt.rcParams['axes.unicode_minus'] = False

    grow_rate_T = grow_rate.T
    
    #  꺾은선 그래프
    # ax = grow_rate_T.plot(kind='bar', figsize=(12,6), width=0.7, colormap='Set2') 막대그래프
    ax = grow_rate_T.plot(kind='line',marker='o', figsize=(12,6), colormap='Set2')

    plt.title('연도별 각 항목의 변화율', fontsize=15)
    plt.ylabel('변화율 (%)')
    plt.xticks(rotation=0)
    plt.legend(title='', loc='right', bbox_to_anchor=(1.1, 0.5))

    plt.tight_layout()
    plt.savefig(save_dir_file, bbox_inches='tight')

if __name__ == "__main__":
    # 테스트용 데이터 입니다 
    data = {
        '2020': [6097, 13461, 3412, 2397, 6013, 3704],
        '2021': [5000, 10000, 3000, 2000, 6000, 3700],
        '2022': [7000, 11000, 3700, 3000, 8000, 4000],
        '2023': [9000, 10000, 4000, 4000, 10000, 6000]
            }
    index_labels = ['정책', '교육', '농사', '스마트',  '인구', '토지']
    df = pd.DataFrame(data, index=index_labels) 

    df1 = pd.read_csv("news_crawl/keywords_change_by_year/keywords_change_by_year.csv" , index_col=0)
    keywords_change_by_year(df1)

