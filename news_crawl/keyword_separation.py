import json
from kiwipiepy import Kiwi
from kiwipiepy.utils import Stopwords
from collections import Counter
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager

# 막대그래프 폰트 (깨져서 설정)
plt.rc('font', family='Malgun Gothic')

kiwi = Kiwi()
stopwords = Stopwords()

with open('C:/Users/admin/Desktop/data-project/news_crawl/crawl_news.json', 'r', encoding='utf-8') as f:
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

plt.show()