import pandas as pd
import os

REGION_MAPPING = {
    # 서울, 인천, 경기
    '서울': '서울', '관악산': '서울', '강남': '서울', '현충원': '서울',
    '인천': '인천', '강화': '인천', '백령도': '인천',
    '수원': '경기', '동두천': '경기', '파주': '경기', '이천': '경기', '양평': '경기',
    '강화': '인천', '양주': '경기', '포천': '경기', '연천': '경기', '가평': '경기',
    
    # 강원
    '속초': '강원', '북춘천': '강원', '철원': '강원', '대관령': '강원', 
    '춘천': '강원', '북강릉': '강원', '강릉': '강원', '동해': '강원', 
    '원주': '강원', '영월': '강원', '인제': '강원', '홍천': '강원', 
    '태백': '강원', '정선군': '강원', '삼척': '강원', '홍천': '강원',
    '양구': '강원', '화천': '강원', '고성': '강원', '양양': '강원',
    
    # 대전, 세종, 충남, 충북
    '대전': '대전',
    '세종': '세종', '세종연서': '세종',
    '청주': '충북', '충주': '충북', '제천': '충북', '보은': '충북', '추풍령': '충북',
    '괴산': '충북', '음성': '충북', '단양': '충북', '증평': '충북',
    '천안': '충남', '서산': '충남', '보령': '충남', '부여': '충남', '금산': '충남', 
    '홍성': '충남', '태안': '충남', '당진': '충남', '아산': '충남', '예산': '충남', '청양': '충남',
    
    # 광주, 전남, 전북
    '광주': '광주',
    '전주': '전북', '군산': '전북', '부안': '전북', '임실': '전북', '정읍': '전북', 
    '남원': '전북', '장수': '전북', '고창': '전북', '순창': '전북', '진안': '전북', '무주': '전북',
    '목포': '전남', '여수': '전남', '순천': '전남', '완도': '전남', '진도(첨찰산)': '전남', 
    '해남': '전남', '고흥': '전남', '강진': '전남', '장흥': '전남', '흑산도': '전남', 
    '광양시': '전남', '진도': '전남', '영광': '전남', '함평': '전남', '나주': '전남', '화순': '전남',
    
    # 부산, 대구, 울산, 경북, 경남
    '부산': '부산',
    '대구': '대구',
    '울산': '울산',
    '포항': '경북', '안동': '경북', '구미': '경북', '영주': '경북', '문경': '경북', 
    '울진': '경북', '영덕': '경북', '의성': '경북', '상주': '경북', '봉화': '경북', 
    '영천': '경북', '청송군': '경북', '경주시': '경북', '울릉도': '경북', '청송': '경북', '경주': '경북',
    '김천': '경북', '칠곡': '경북', '성주': '경북', '고령': '경북', '예천': '경북',
    '창원': '경남', '진주': '경남', '통영': '경남', '거제': '경남', '밀양': '경남', 
    '산청': '경남', '합천': '경남', '거창': '경남', '남해': '경남', '북창원': '경남', 
    '양산시': '경남', '의령': '경남', '함안': '경남', '창녕': '경남', '고성': '경남', '하동': '경남',
    
    # 제주
    '제주': '제주', '서귀포': '제주', '성산': '제주', '고산': '제주'
}


# SPI 일별 -> 월별 변환 및 전처리
def spi_process(spi):
    df = pd.read_csv(spi, encoding='cp949')

    date_cal = df.columns[2]
    df[date_cal] = pd.to_datetime(df[date_cal])

    station_col = df.columns[1]

    df_monthly = df.groupby([station_col, pd.Grouper(key=date_cal, freq='M')]).mean(numeric_only=True).reset_index()

    df_monthly.rename(columns={station_col: '지점명'}, inplace=True)

    df_monthly['일시'] = pd.to_datetime(df_monthly['일시'])
    df_monthly['연도'] = df_monthly['일시'].dt.year
    df_monthly['월'] = df_monthly['일시'].dt.month
    print(df_monthly.head())
    df_monthly.to_csv('processed_spi.csv', index=False, encoding='utf-8')
    return df_monthly



def merge_spi_weather(spi, weather_file):
    weather = pd.read_csv(weather_file, encoding='cp949')
    
    weather['일시'] = pd.to_datetime(weather['일시'])
    weather['연도'] = weather['일시'].dt.year
    weather['월'] = weather['일시'].dt.month

    #SPI는 3개월, 6개월 지수만 사용
    spi_cols = ['지점명','연도', '월', 'SPI3', 'SPI6']

    merge = pd.merge(
        weather,
        spi[spi_cols],
        on=['지점명', '연도', '월'],
        how='inner'
    )

    merge['시도'] = merge['지점명'].map(REGION_MAPPING)
    merge = merge[merge['시도'].notnull()].copy()

    fill_zero_cols = ['월합강수량(00~24h만)(mm)', '최심적설(cm)', '합계 일조시간(hr)']
    for col in fill_zero_cols:
        if col in merge.columns:
            merge[col] = merge[col].fillna(0)
    
    return merge






if __name__ == "__main__":
    SPI = '표준강수지수.csv'
    Weather = '날씨.csv'



    if os.path.exists(SPI) and os.path.exists(Weather):
        new_spi = spi_process(SPI)
        merged_df = merge_spi_weather(new_spi, Weather)

        merged_df.to_csv('merged_weather_spi.csv', index=False, encoding='utf-8')

        
        
    else:
        print("필요한 파일이 존재하지 않습니다.")
        