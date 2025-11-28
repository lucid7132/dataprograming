import re
import json
from argparse import ArgumentParser, Namespace
from copy import deepcopy
from multiprocessing.pool import Pool
from time import sleep
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests
from pandas import date_range
from tqdm import tqdm
from trafilatura import extract, fetch_url
from trafilatura.settings import DEFAULT_CONFIG


# ==========================
# 1. 실행 인자 설정
# ==========================
argparser = ArgumentParser("네이버 뉴스 크롤링")

argparser.add_argument("--query", type=str, default="귀농")         # 검색어
argparser.add_argument("--start-date", type=str, default="2025.10.01")  # 시작 날짜 (YYYY.MM.DD)
argparser.add_argument("--end-date", type=str, default="2025.10.31")    # 끝 날짜 (YYYY.MM.DD)

argparser.add_argument("--num-workers", type=int, default=10)      # 병렬 처리 프로세스 수
argparser.add_argument("--max-trials", type=int, default=3)        # 요청 재시도 횟수
argparser.add_argument("--sleep-time", type=float, default=0.5)    # 요청 사이 대기 시간(초)

# 선택: 직접 파일명을 지정하고 싶으면 사용 (지정 안 하면 "키워드.json" 자동 생성)
argparser.add_argument("--output-path", type=str, default="")      # 비워두면 자동으로 "키워드.json" 사용


# ==========================
# 2. 공통 설정
# ==========================

# 네이버에서 봤을 때 "브라우저처럼" 보이게 하는 헤더
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# trafilatura 설정
TRAFILATURA_CONFIG = deepcopy(DEFAULT_CONFIG)
TRAFILATURA_CONFIG["DEFAULT"]["DOWNLOAD_TIMEOUT"] = "5"   # 5초 넘으면 포기
TRAFILATURA_CONFIG["DEFAULT"]["MIN_OUTPUT_SIZE"] = "50"   # 본문 50자 미만이면 버림


# ==========================
# 3. 기사 1개 본문 추출 함수
# ==========================

def get_article_body(url: str) -> Optional[Dict[str, Any]]:
    """
    기사 URL 1개를 받아서
    - trafilatura로 본문을 추출하고
    - title, text, url만 담아서 리턴
    실패하면 None 반환
    """
    try:
        downloaded = fetch_url(url, config=TRAFILATURA_CONFIG)
        if not downloaded:
            return None

        extracted = extract(
            downloaded,
            output_format="json",
            target_language="ko",
            with_metadata=True,
            deduplicate=True,
            config=TRAFILATURA_CONFIG,
        )
        if extracted is None:
            return None

        data = json.loads(extracted)

        title = (data.get("title") or "").strip()
        text = (data.get("text") or "").strip()
        source_url = data.get("source") or url

        # 본문이 아예 없으면 버림
        if not text:
            return None

        return {
            "title": title,
            "text": text,
            "url": source_url,
        }

    except KeyboardInterrupt:
        exit()
    except Exception:
        # 에러 나면 조용히 None
        return None


# ==========================
# 4. 전체 날짜 범위 크롤링
# ==========================

def crawl_articles(args: Namespace) -> List[Dict[str, str]]:
    """
    날짜 범위 + 검색어에 대해
    네이버 뉴스 검색 API를 호출하고,
    각 기사 본문을 수집해서 리스트로 반환.
    """
    # 날짜 리스트 생성
    dates = date_range(args.start_date, args.end_date, freq="D")

    # 검색어 URL 인코딩
    encoded_query = quote(args.query)

    articles: List[Dict[str, str]] = []

    progress_bar = tqdm(total=len(dates))

    for date in dates:
        date_str = date.strftime("%Y%m%d")

        # 네이버 모바일 뉴스 검색 "더보기" API URL 형식
        next_url = (
            "https://s.search.naver.com/p/newssearch/3/api/tab/more?"
            f"query={encoded_query}&sort=0&"
            f"nso=so%3Ar%2Cp%3Afrom{date_str}to{date_str}%2Ca%3Aall&"
            f"ssc=tab.m_news.all&"
            f"start=1"
        )

        prev_count = len(articles)

        while True:
            num_trials = 0
            response = None

            # 요청 재시도 로직
            while num_trials < args.max_trials:
                try:
                    response = requests.get(
                        next_url,
                        headers=HEADERS,
                        timeout=5,
                    )
                    break
                except KeyboardInterrupt:
                    exit()
                except Exception:
                    sleep(args.sleep_time)
                    num_trials += 1

            if response is None:
                break

            # JSON 파싱
            try:
                result = response.json()
            except Exception:
                # JSON이 아니면 (캡차 등) 종료
                break

            # collection 없거나 비어 있으면 뉴스 없음
            collection = result.get("collection")
            if not collection:
                break

            # 다음 페이지 URL
            next_url = result.get("url", "")
            if not next_url:
                # 마지막 페이지
                break

            # script 에서 기사 URL 추출
            script = collection[0].get("script", "")
            article_urls = re.findall(r"\"contentHref\":\"(.*?)\"", script)

            if not article_urls:
                # 이 페이지에 기사 URL이 없으면 종료
                break

            # 멀티프로세스로 기사 본문 수집
            with Pool(args.num_workers) as pool:
                for article_body in pool.imap_unordered(get_article_body, article_urls):
                    if article_body is not None:
                        articles.append(article_body)

            progress_bar.set_postfix(
                {"date": date_str, "total_articles": len(articles)}
            )

            sleep(args.sleep_time)

        # 날짜별 수집 개수
        daily_added = len(articles) - prev_count
        # print(f"{date_str}: {daily_added}개 수집")

        progress_bar.update(1)

    progress_bar.close()
    return articles


# ==========================
# 5. 메인 실행 부분
# ==========================

def make_output_path(args: Namespace) -> str:
    """
    output-path를 지정했으면 그걸 쓰고,
    지정 안 했으면 query를 이용해서 `키워드.json` 파일 이름을 만든다.
    예) query="강원 귀농" → "강원 귀농.json"
        (윈도우에서 안 되는 특수문자는 '_'로 치환)
    """
    if args.output_path:
        return args.output_path

    # query 기반 자동 파일명
    filename = args.query.strip()
    if not filename:
        filename = "news"

    # 윈도우에서 문제되는 문자 치환
    # \ / : * ? " < > |  → _
    filename = re.sub(r'[\\/:*?"<>|]', "_", filename)

    return f"{filename}.json"


if __name__ == "__main__":
    args = argparser.parse_args()

    print(f"검색어: {args.query}")
    print(f"날짜: {args.start_date} ~ {args.end_date}")


    crawled_articles = crawl_articles(args)

    # 기사 하나도 못 모았을 때: [] 대신 "기사 없음" 메시지 한 개 넣기
    if len(crawled_articles) == 0:
        print("※ 해당 기간에 수집된 기사가 없습니다. '기사 없음' 메시지 하나를 JSON에 저장합니다.")
        crawled_articles = [
            {
                "title": f"'{args.query}'에 대한 기사가 없습니다.",
                "text": "",
                "url": "",
            }
        ]

    output_path = make_output_path(args)

    print(f"총 {len(crawled_articles)}개의 데이터를 저장합니다 → {output_path}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(crawled_articles, f, ensure_ascii=False, indent=2)
