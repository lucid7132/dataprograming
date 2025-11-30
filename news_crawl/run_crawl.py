import json
import os
from types import SimpleNamespace       # 인자값 전달을 위함
from naver_news_crawl import crawl_news # 기존파일 함수
from typing import List, Dict

# 크롤링 함수의 설정(인자)값
# 원하는 주제, 파일명을 configs 에 추가 후 실행
# 실행 후 시작연도 종료연도를 입력해주세요. 종료연도를 포합합니다. 범위 : 1900~2025
# 연도별로 크롤링을 시작 및 저장합니다. 
# 결과값은 crawl_result/{filename}_{year}.json에 저장됩니다. 

# configs 예시입니다. 

'''
{
        "query": "귀농",
        "filename": "return_farming_news"
},
{
        "query": "축제",
        "filename": "festival"
}
    {
        
    }
    {
        "query": "귀농경상북도",
        "filename": "farming_gybok"
    }
'''

configs = [
    {
        "query": "귀농전라남도",
        "filename": "farming_jnam"
    }
]

def run_crawl(year:int , config:List[Dict]):
    # 저장할 위치 & 생성
    save_dir = "news_crawl/crawl_result"
    os.makedirs(save_dir, exist_ok=True)

    start_date = f"{year}.01.01"
    end_date = f"{year}.12.30"
    output_path = f"{config["filename"]}_{year}.json"

    print(f"{config['query']}_{year} 크롤링 시작")

    # argparse 의 인자처리를 위한 코드
    args = SimpleNamespace(
        query=config["query"],
        start_date=start_date,
        end_date=end_date,
        output_path=output_path,
        num_processes=10,
        sleep_time=0.5,
        max_trials=3
    )
    
    # 크롤링 시작 
    news_date = crawl_news(args)

    save_path = os.path.join(save_dir, output_path)

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(news_date, f, ensure_ascii=False, indent=4)
    
    print(f"{config['query']}_{year} 저장완료")

if __name__ == "__main__":
    try:
        while True:
            print("크롤링할 연도를 입력해주세요. 예 : 2020 2025")
            print("종료 : Ctrl + C")
            
            start_year, end_year = map(int, input().split())

            if start_year > end_year:
                print("시작연도가 더 큽니다. 다시입력해주세요. \n")
                continue
            if 1900 > start_year or start_year > 2026:
                print("시작연도가 잘못되었습니다. 범위 : 1900~2025 \n")
                continue
            if 1900 > end_year or end_year > 2026:
                print("종료연도가 잘못되었습니다. 범위 : 1900~2025 \n")
                continue
            break
        for config in configs:
            for year in range(start_year, end_year+1):
                run_crawl(year, config)

    except KeyboardInterrupt:
            print("프로그램을 종료합니다. ")