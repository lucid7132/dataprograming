import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib.font_manager as fm


plt.rcParams['font.family'] ='Malgun Gothic'
plt.rcParams['axes.unicode_minus'] =False



def load_and_preprocess(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except:
        try:
            df = pd.read_csv(file_path, encoding='cp949')
        except:
            df = pd.read_csv(file_path, encoding='euc-kr')
    
    # 각 지점을 해당하는 시도로 묶음
    region_map = {
        '속초': '강원', '북춘천': '강원', '철원': '강원', '대관령': '강원', '춘천': '강원', 
        '북강릉': '강원', '강릉': '강원', '동해': '강원', '원주': '강원', '영월': '강원', 
        '인제': '강원', '홍천': '강원', '태백': '강원', '정선군': '강원',


        '안동': '경북', '상주': '경북', '포항': '경북', '영주': '경북', '문경': '경북', 
        '청송군': '경북', '영덕': '경북', '의성': '경북', '구미': '경북', '영천': '경북', 
        '경주시': '경북', '봉화': '경북', '울진': '경북', '울릉도': '경북',


        '목포': '전남', '여수': '전남', '순천': '전남', '광양시': '전남', '보성군': '전남', 
        '강진군': '전남', '장흥': '전남', '해남': '전남', '고흥': '전남', '영광군': '전남', 
        '완도': '전남', '진도군': '전남', '흑산도': '전남', '진도(첨찰산)': '전남',


        '창원': '경남', '진주': '경남', '통영': '경남', '김해시': '경남', '밀양': '경남', 
        '거제': '경남', '양산시': '경남', '의령군': '경남', '함양군': '경남', '거창': '경남', 
        '합천': '경남', '산청': '경남', '남해': '경남', '북창원': '경남'
    }

    df['시도'] = df['지점명'].map(region_map)
    df = df[df['시도'].notnull()].copy()

    #계절을 분류하기 위해 '월'열 생성
    df['일시'] = pd.to_datetime(df['일시'])
    df['연도'] = df['일시'].dt.year
    df['월'] = df['일시'].dt.month

    #결측값 처리
    fill_zero_cols = ['월합강수량(00~24h만)(mm)', '최심적설(cm)', '합계 일조시간(hr)']
    for col in fill_zero_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)
            
    #해당 csv가 2023년 1월 데이터 밖에 없어서 22년도 까지 데이터 범위 축소
    df = df[df['연도'] < 2023].copy()

    return df



#해당 season의 feature값들의 op값
def preprocessing_weather(df, feature='', season='연간'):

    # 계절 분류
    if season == '여름':
        target_months = [6, 7, 8]
        prefix = '여름_'
    elif season == '겨울':
        target_months = [12, 1, 2]
        prefix = '겨울_'
    elif season == '봄':
        target_months = [3, 4, 5]
        prefix = '봄_'
    elif season == '가을':
        target_months = [9, 10, 11]
        prefix = '가을_'
    else:
        target_months = list(range(1, 13))
        prefix = '연_'
    
    
    df_seasonal = df[df['월'].isin(target_months)].copy()


    df_spatial = df_seasonal.groupby(['연도', '시도', '월']).agg({
        '월합강수량(00~24h만)(mm)': 'mean',
        '평균기온(°C)': 'mean',
        '최저기온(°C)': 'mean',
        '평균풍속(m/s)': 'mean',
        '합계 일조시간(hr)': 'mean',
        '최심적설(cm)': 'max'
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
            '합계 일조시간(hr)': 'sum',
            '최심적설(cm)': 'max'
        }).reset_index()

        df_result.columns = [
            '연도', '시도', '연강수량', '연평균기온',
            '연최저기온', '연평균풍속', '연일조시간', '최대적설'
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
        elif feature == '적설량':
            op = 'max'; col_name = '최심적설(cm)'
        elif feature == '최저기온':
            op = 'mean'; col_name = '최저기온(°C)'
        
        df_result = df_spatial.groupby(['연도', '시도']).agg({
            col_name: op
        }).reset_index()
        
        
        target_col = f'{prefix}{feature}'
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
            ('연일조시간', f'[{season}] 총 일조시간 (hr)'),
            ('최대적설', f'[{season}] 최대 적설심 (cm)')
        ]

        for i, (col, title) in enumerate(metrics):
            row, col_idx = divmod(i, 2)
            ax = axes[row, col_idx]
            sns.lineplot(data=df, x='연도', y=col, hue='시도', style='시도', 
                         palette=colors, markers=True, linewidth=2.5, ax=ax)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
        

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
    file_name = 'OBS_ASOS_MNH_20251119143018.csv'
    
    # 원하는 계절 입력하면 해당 계절만 보여줌 4계절이 아니라면 연 단위로 보여줌
    season = '여름'

    # 옵션은 강수량, 평균기온, 최저기온, 평균풍속, 일조시간, 적설량만 입력가능
    # 빈문자열이면 5개 모두 출력함
    feature = ''     
    
    if os.path.exists(file_name):
        
        df_raw = load_and_preprocess(file_name)
        
        df_final, target_col, is_default = preprocessing_weather(df_raw, feature, season)  #aggregate_date(csv파일, 조건, 계절)
        
        print(f"--- [{season}] 데이터 미리보기 ---")
        print(df_final.head())

        visualization(df_final, feature, season, target_col, is_default)
    else:
        print("파일을 찾을 수 없습니다.")