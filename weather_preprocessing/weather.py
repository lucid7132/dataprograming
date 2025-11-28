import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False

#해당 season의 feature값들의 op값
def preprocessing_weather(df, feature='', season='연간'):

    # 계절 분류
    if season == '여름':
        target_months = [6, 7, 8]
    elif season == '겨울':
        target_months = [12, 1, 2]
    elif season == '봄':
        target_months = [3, 4, 5]
    elif season == '가을':
        target_months = [9, 10, 11]
    else:
        target_months = list(range(1, 13))
    
    
    df_seasonal = df[df['월'].isin(target_months)].copy()

    df_spatial = df_seasonal.groupby(['연도', '시도', '월']).agg({
        '월합강수량(00~24h만)(mm)': 'mean',
        '평균기온(°C)': 'mean',
        '최저기온(°C)': 'mean',
        '평균풍속(m/s)': 'mean',
        '합계 일조시간(hr)': 'mean'
    }).reset_index()

    # feature가 빈 문자열인지 판단
    is_default_mode = (feature == '')

    # feature가 빈 문자열일 경우 모든 feature 데이터 생성
    if is_default_mode:
        
        df_result = df_spatial.groupby(['연도', '시도']).agg({
            '월합강수량(00~24h만)(mm)': 'sum', 
            '평균기온(°C)': 'mean',
            '최저기온(°C)': 'mean',
            '평균풍속(m/s)': 'mean',
            '합계 일조시간(hr)': 'sum'
        }).reset_index()

        df_result.columns = [
            '연도', '시도', '연강수량', '연평균기온',
            '연최저기온', '연평균풍속', '연일조시간'
        ]
        target_col = None

    # feature가 정해져 있다면 해당 feature만 데이터 생성
    else:
        if feature == '강수량':
            op = 'sum'; col_name = '월합강수량(00~24h만)(mm)'
        elif feature == '평균기온':
            op = 'mean'; col_name = '평균기온(°C)'
        elif feature == '평균풍속':
            op = 'mean'; col_name = '평균풍속(m/s)'
        elif feature == '일조시간':
            op = 'sum'; col_name = '합계 일조시간(hr)'
        elif feature == '최저기온':
            op = 'mean'; col_name = '최저기온(°C)'
        
        df_result = df_spatial.groupby(['연도', '시도']).agg({
            col_name: op
        }).reset_index()
        
        
        target_col = f'{season}_{feature}'
        df_result = df_result.rename(columns={col_name: target_col})

    # 해당 인자로 전처리 된 csv, 해당 feature, feature 빈 문자열 판단 
    return df_result, target_col, is_default_mode


def visualization(df, feature, season, target_col, is_default_mode):
    colors = {'강원': 'blue', '전남': 'green', '경북': 'orange', '경남': 'red'}

    if is_default_mode:
        
        fig, axes = plt.subplots(3, 2, figsize=(18, 15))
        metrics = [
            ('연강수량', f'[{season}] 총 강수량 (mm)'),
            ('연평균기온', f'[{season}] 평균 기온 (°C)'),
            ('연최저기온', f'[{season}] 최저 기온 (°C)'),
            ('연평균풍속', f'[{season}] 평균 풍속 (m/s)'),
            ('연일조시간', f'[{season}] 총 일조시간 (hr)')
        ]

        for i, (col, title) in enumerate(metrics):
            row, col_idx = divmod(i, 2)
            ax = axes[row, col_idx]
            sns.lineplot(data=df, x='연도', y=col, hue='시도', style='시도', 
                         palette=colors, markers=True, linewidth=2.5, ax=ax)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
        # 마지막 빈 그래프 제거
        axes[2, 1].axis('off')
        
    # feature 문자열이 빈 문자열이 아닐 때
    else:
        plt.figure(figsize=(12, 6))
        sns.lineplot(data=df, x='연도', y=target_col, hue='시도', style='시도', 
                     palette=colors, markers=True, linewidth=3)
        
        plt.title(f'[{season}] {feature} 비교 분석', fontsize=18, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.ylabel(feature)
    
    if is_default_mode:
        plt.suptitle(f'강원도, 상위 3지역 [{season}] 기후 종합 비교', fontsize=20, fontweight='bold')
    
    plt.tight_layout()
    plt.show()


# 메인 함수
if __name__ == "__main__":
    file_name = 'merged_weather_spi.csv'
    
    # 원하는 계절 입력하면 해당 계절만 보여줌 4계절이 아니라면 연 단위로 보여줌
    season = '겨울'

    # 옵션은 강수량, 평균기온, 최저기온, 평균풍속, 일조시간만 입력가능
    # 빈문자열이면 5개 모두 출력함
    feature = ''     
    
    if os.path.exists(file_name):
        
        df_raw = pd.read_csv(file_name, encoding='utf-8')
        regions = ['강원', '전남', '경북', '경남']
        df_raw = df_raw[df_raw['시도'].isin(regions)].copy()
        df_final, target_col, is_default = preprocessing_weather(df_raw, feature, season)  #aggregate_date(csv파일, 조건, 계절)
        
        visualization(df_final, feature, season, target_col, is_default)
    else:
        print("파일을 찾을 수 없습니다.")