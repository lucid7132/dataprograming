import json
import os
from types import SimpleNamespace       # 인자값 전달을 위함
from naver_news_crawl import crawl_news # 기존파일 함수

# 크롤링 함수의 설정(인자)값
# 원하는 주제, 기간, 파일명을 configs 에 추가 후 실행
# 결과값은 crawl_result/{filename}.json에 저장됩니다. 

# configs 예시입니다. 
"""
    {
        "query": "작물",
        "start_date": "2025.11.20",
        "end_date": "2025.11.21",
        "filename": "crops_news.json"
    }
"""

configs = [
    {
        "query": "귀농",
        "start_date": "2020.01.01",
        "end_date": "2020.06.30",
        "filename": "return_farming_news_202001_06.json"
    },
    {
        "query": "귀농",
        "start_date": "2020.07.01",
        "end_date": "2020.12.30",
        "filename": "return_farming_news_202006_12.json"
    }
]

def run_crawl():
    # 저장할 위치 & 생성
    save_dir = "news_crawl/crawl_result"
    os.makedirs(save_dir, exist_ok=True)

    for config in configs:
        print(f"{config['query']} 크롤링 시작")

        # argparse 의 인자처리를 위한 코드
        args = SimpleNamespace(
            query=config["query"],
            start_date=config["start_date"],
            end_date=config["end_date"],
            output_path=config["filename"],
            num_processes=10,
            sleep_time=0.5,
            max_trials=3
        )
        
        news_date = crawl_news(args)

        save_path = os.path.join(save_dir, config["filename"])

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(news_date, f, ensure_ascii=False, indent=4)
        
        print(f"{config["query"]} 저장완료")

if __name__ == "__main__":
    run_crawl()