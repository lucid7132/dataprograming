import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import json
from time import sleep
from argparse import ArgumentParser
from trafilatura import fetch_url, extract
from trafilatura.settings import DEFAULT_CONFIG
from copy import deepcopy


# -----------------------------
# 1. 실행 인자
# -----------------------------
parser = ArgumentParser("네이버 뉴스 HTML 기반 크롤러")
parser.add_argument("--query", type=str, default="귀농")
parser.add_argument("--start-date", type=str, default="2025.10.01")
parser.add_argument("--end-date", type=str, default="2025.10.31")
parser.add_argument("--sleep", type=float, default=0.5)
parser.add_argument("--output", type=str, default="")
args = parser.parse_args()


# -----------------------------
# 2. 날짜 변환 함수
# -----------------------------
def convert_date(d: str) -> str:
    """2025.10.01 → 20251001 형태로 변환"""
    return d.replace(".", "")


start = convert_date(args.start_date)
end = convert_date(args.end_date)

encoded_query = quote(args.query)


# -----------------------------
# 3. trafilatura 설정
# -----------------------------
TR_CONFIG = deepcopy(DEFAULT_CONFIG)
TR_CONFIG["DEFAULT"]["DOWNLOAD_TIMEOUT"] = "5"
TR_CONFIG["DEFAULT"]["MIN_OUTPUT_SIZE"] = "50"


# -----------------------------
# 4. 기사 본문 추출 함수
# -----------------------------
def get_body(url: str):
    try:
        downloaded = fetch_url(url, config=TR_CONFIG)
        if not downloaded:
            return None

        extracted = extract(
            downloaded,
            output_format="json",
            target_language="ko",
            with_metadata=True,
            deduplicate=True,
            config=TR_CONFIG,
        )

        if extracted is None:
            return None

        data = json.loads(extracted)
        return {
            "title": data.get("title", "").strip(),
            "text": data.get("text", "").strip(),
            "url": url,
        }
    except:
        return None


# -----------------------------
# 5. HTML 기반 뉴스 검색
# -----------------------------
def crawl_news():
    page = 1
    articles = []

    while True:
        url = (
            "https://search.naver.com/search.naver"
            f"?where=news&query={encoded_query}"
            f"&pd=3&ds={args.start_date}&de={args.end_date}"
            f"&start={page}"
        )

        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        news_items = soup.select("a.news_tit")  # 뉴스 제목 링크

        if not news_items:
            break  # 더 이상 뉴스 없음 → 종료

        for item in news_items:
            link = item["href"]
            body = get_body(link)
            if body:
                articles.append(body)

        page += 10  # 다음 페이지
        sleep(args.sleep)

    return articles


# -----------------------------
# 6. 실행
# -----------------------------
news_list = crawl_news()

if not news_list:
    news_list = [{"title": "기사 없음", "text": "", "url": ""}]

filename = f"{args.query}.json" if not args.output else args.output

# 윈도우 특수문자 제거
filename = filename.replace("/", "_").replace("\\", "_").replace(" ", "_")

with open(filename, "w", encoding="utf-8") as f:
    json.dump(news_list, f, ensure_ascii=False, indent=2)

print(f"총 {len(news_list)}개 기사 저장 완료 → {filename}")
