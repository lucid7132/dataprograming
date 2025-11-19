import re
from copy import deepcopy
from urllib.parse import quote                  # 유니코드 url escape 변환
from argparse import ArgumentParser, Namespace  # 실행시 인자를 넣어줄수 있음 
from typing import List, Dict, Any, Optional
from multiprocessing.pool import Pool
from time import sleep

import json 
import requests
from trafilatura import fetch_url, extract
from trafilatura.settings import DEFAULT_CONFIG # trafilatura 설정
from pandas import date_range                   # 날짜 리스트 받기 
from tqdm import tqdm

# 네이버 뉴스 크롤링
# 크롤링한 파일 생성 : 파일명 crawl_news.json
# json 파일 내 title, text로 분리 

# 추후 고려 사항 - 연도별로 구분?
#   년단위로 기사가 증가?감소?

argparser = ArgumentParser("네이버 뉴스 크롤링")
argparser.add_argument("--query", type=str, default="귀농")
argparser.add_argument("--start-date", type=str, default="2025.11.17")
argparser.add_argument("--end-date", type=str, default="2025.11.17")
argparser.add_argument("--output-path", type=str, default="crawl_news.json")
argparser.add_argument("--num-processes", type=int, default=10)             # 멀티프로세싱 갯수
argparser.add_argument("--sleep-time", type=float, default=0.5)             # 매 시도 마다 기다릴시간
argparser.add_argument("--max-trials", type=int, default=3)                 # 최대 재시도 횟수 

TRAFILATURA_CONFIG = deepcopy(DEFAULT_CONFIG)
# URL에 대해서 5초 이상 다운로드를 기다리지 않음
TRAFILATURA_CONFIG["DEFAULT"]["DOWNLOAD_TIMEOUT"] = "5"
# 최소 본문 길이가 50자 이상인 경우에만 사용
TRAFILATURA_CONFIG["DEFAULT"]["MIN_OUTPUT_SIZE"] = "50"

def crawl_one_news_page(url: str) -> Optional[Dict[str, Any]]:
    try:
        downloaded = fetch_url(url, config=TRAFILATURA_CONFIG)            
    
        news_content = json.loads(
            extract(
                downloaded,
                output_format="json",
                with_metadata=True,
                target_language="ko",
                deduplicate=True,
                config=TRAFILATURA_CONFIG,
            )
        )
        return news_content
    
    # trafilatura.extract 가 본문을 못읽으면 타입에러 
    except TypeError: 
        print(f"본문추출실패-{url}")
        return None


def crawl_news(args: Namespace) -> List[Dict[str, str]]:

    """
    아래 주석은 인자 default값으로 처리함
    query = "귀농"
    start_date = "20251104"
    end_date = "20251104"
    """

    # url 쿼리 인코딩
    encoded_query = quote(args.query)

    # 날짜범위 생성
    date_list = date_range(args.start_date, args.end_date, freq="D")

    # 리턴할 값을 담을 뉴스데이터 리스트 
    news_data = []

    with tqdm(total=len(date_list)) as progress_bar:
        for date in date_list:

            date_str = date.strftime("%Y%m%d")

            # query sorte nso ssc start 중요인자
            next_url = (
                "https://s.search.naver.com/p/newssearch/3/api/tab/more?"
                f"query={encoded_query}&sort=0&"
                f"nso=so%3Ar%2Cp%3Afrom{date_str}to{date_str}%2Ca%3Aall&ssc=tab.news.all&"
                f"start=1"
            )

            while True:
                num_trials = 0
                while num_trials < args.max_trials: # 인자로 받은 횟수만큼 시도 
                    try:
                        response = requests.get(next_url)
                        break
                    except KeyboardInterrupt: # ctrl + c 로 종료
                        exit()
                    except Exception as e: # 기타 이유로 실패시 sleep_time대기후 재시도
                        print(f"기타 이유로 {args.sleep_time}초 후 재시도 : {next_url}")
                        sleep(args.sleep_time)
                        num_trials += 1
                
                r_data = response.json()
                # 빈 url 이면 collection이 공백(None)
                if "collection" not in r_data or r_data["collection"] is None: 
                    break

                next_url = r_data["url"]
                if next_url == "":
                    print("마지막 페이지 도달")
                    break
                
                script_source = r_data["collection"][0]["script"]
                
                #뉴스기사의 url 정규표현식
                news_urls = re.findall(r"\"contentHref\":\"(.*?)\"", script_source)

                with Pool(args.num_processes) as pool:
                    # pool을 통해 나온 리턴값을 컨텐츠에 담음 
                    for news_content in pool.imap_unordered(crawl_one_news_page, news_urls): 
                        if news_content is None:
                            continue
                        title = news_content["title"]
                        text = news_content["text"]
                        news_data.append({"title":title, "text":text})

                progress_bar.set_postfix({"date": date, "num_Article":len(news_data)})
                sleep(args.sleep_time)

            progress_bar.update(1)

    return news_data

if __name__ == "__main__":
    args = argparser.parse_args() 

    news_data = crawl_news(args)

    with open("news_crawl/crawl_news.json", "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False) #유니코드 변환 방지