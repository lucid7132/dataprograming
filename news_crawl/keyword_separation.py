import os
import json
from kiwipiepy import Kiwi
from kiwipiepy.utils import Stopwords
from collections import Counter
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager

# 크롤링한 뉴스 json파일을 키워드 분석합니다 
# + 뉴스 전처리 필요 ( 기자이름, 이메일, ~ 무단배포 머시기 제외 

# 막대그래프 폰트 (깨져서 설정)
plt.rc('font', family='Malgun Gothic')

kiwi = Kiwi()
stopwords = Stopwords()
stopwords.add(("귀농", "NNG"))
stopwords.add(("귀촌", "NNG"))

dir_path = "news_crawl/crawl_result"
all_json = os.listdir(dir_path)


def keyword_separation(file):
    
    # json 폴더 경로 + 파일이름 
    file_path = os.path.join(dir_path, file)

    # 확장자명 json -> png 로 변경 ( 시각화 .png 파일 저장 위치용도)
    file_no_json = os.path.splitext(os.path.basename(file_path))[0]
    file_no_json = f"{file_no_json}.png"
    png_path = os.path.join("news_crawl", file_no_json)

    with open(file_path, 'r', encoding='utf-8') as f:
        news_data = json.load(f)

    # print(news_data[0]["title"])

    counter = Counter()
    tags = {"NNG", "NNP", "VV", "VA", "SL"}

    # mininterval 업데이트 간격 
    for news in tqdm(news_data, total=len(news_data), mininterval=1):
        body_text = news["text"].strip()
        if len(body_text) < 10:
            continue

        # 불용어 제거, 특정 품사이면서 길이가 2 이상인 단어만 추출
        tokens = [
            pos.form
            for pos in kiwi.tokenize(body_text, normalize_coda=True, stopwords=stopwords)
            if pos.tag in tags and len(pos.form) > 1
        ]
        counter.update(tokens)

    # 상위 n개 단어 빈도 출력
    top_num = 50

    # for word, count in counter.most_common(top_num): print(word, count)

    top_words = counter.most_common(top_num)
    words = [w for w, c in top_words]
    counts = [c for w, c in top_words]

    # 막대 그래프 시각화
    plt.figure(figsize=(10, max(6, top_num * 0.35)))  
    plt.barh(words[::-1], counts[::-1])  
    plt.xlabel("Count")
    plt.ylabel("word")
    plt.title(f"Top {top_num} words")
    plt.tight_layout()
    plt.savefig(png_path)
    plt.show()

    return 0;

if __name__ == "__main__":
    for file in all_json:
        keyword_separation(file)