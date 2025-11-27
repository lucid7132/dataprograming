import os
import json
import re
from kiwipiepy import Kiwi
from kiwipiepy.utils import Stopwords
from collections import Counter
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager

from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfTransformer
from scipy.sparse import dok_matrix
import numpy as np

# 크롤링한 뉴스 json파일을 분석합니다 
# 뉴스 전처리 -> 키워드 분석 -> 토픽 모델링 

# 막대그래프 폰트 (깨져서 설정)
plt.rc('font', family='Malgun Gothic')

dir_path = "news_crawl/crawl_result"
all_json = os.listdir(dir_path)

def news_preprocessing(news_data) -> list:
    documents = []
    invalid_line_patterns = re.compile(
        r"무단\s*전재|배포\s*금지|Copyrights|관련기사|기사\s*제보|여러분의 제보|카카오톡\s*:s*"
    )

    for article in tqdm(news_data, mininterval=1):
        text = article["text"]

        lines = text.split("\n")
        filtered_lines = []

        for line in lines:
            line = " ".join(line.split())

            # OOO 기자 패턴 제거
            line = re.sub(r"\w+ 기자", "", line)
            # email 주소 제거
            line = re.sub(r"\w+@\w+\.\w+", "", line)
            # 뉴스에서 []는 [논산] [대구=뉴시스] 등 다양한 참조를 의미하므로 제거
            line = re.sub(r"\[.*\]", "", line)
            # (서울=연합뉴스) 같은 패턴 제거
            line = re.sub(r"\(.*=.*\)", "", line)
            # 2024.10.29/뉴스1 같은 패턴 제거
            line = re.sub(r"\d{4}\.\d{2}\.\d{2}/.*\b", "", line)

            # 공백 제거
            line = " ".join(line.split())
            
            if invalid_line_patterns.search(line):
                # 무단전재, 배포금지 등이 포함된 문장 이후 문장들은 제외
                break

            # 한국어가 10자 이상 포함된 경우만 포함
            num_korean_chars = len(re.findall(r"[ㄱ-ㅎ가-힣]", line))
            if num_korean_chars >= 10:
                filtered_lines.append(line)

        text = "\n".join(filtered_lines)
        # 한국어가 10자 이상 포함된 경우만 포함
        num_korean_chars = len(re.findall(r"[ㄱ-ㅎ가-힣]", text))
        if num_korean_chars >= 50:
            documents.append(text)

    # 중복 제거
    documents = list(set(documents))

    return documents

def topic_modeling(counter: Counter, tokens_list: list, file_no_json: str):
   
    vocab = [word for word, _ in counter.most_common(10000)]
    word2idx = {word: idx for idx, word in enumerate(vocab)}

    dtm = dok_matrix((len(tokens_list), len(vocab)), dtype=np.float32)

    for doc_idx, tokens in enumerate(tqdm(tokens_list, mininterval=1)):
        for token in tokens:
            try:
                word_idx = word2idx[token]
                dtm[doc_idx, word_idx] += 1
            except KeyError:
                pass

    dtm = dtm.tocsr()
    #print(dtm.shape)

    tfidf = TfidfTransformer()
    tfidf_matrix = tfidf.fit_transform(dtm)

    # 추려낼 토픽 갯수 
    num_topics = 10
    nmf = NMF(n_components=num_topics, max_iter=1000, shuffle=True, random_state=42)

    W = nmf.fit_transform(tfidf_matrix)
    H = nmf.components_

    #print(nmf.n_iter_)
    #print(W.shape, H.shape)   

    # Topic 별로 가장 가중치 높은 단어 10개 저장 
    file_no_json = f"{file_no_json}.txt"
    txt_path = os.path.join("news_crawl/keyword_result", file_no_json)
    with open(txt_path, 'w', encoding='utf-8') as f:
        for topic_idx in range(num_topics):
            top_word_indices = H[topic_idx].argsort()[::-1][:10]
            top_words = [vocab[idx] for idx in top_word_indices]
            f.write(f"Topic #{topic_idx}: {', '.join(top_words)}\n")


def keyword_separation(file: str):

    # json 폴더 경로 + 파일이름 
    file_path = os.path.join(dir_path, file)

    # 확장자 json 없는 파일명 저장 
    file_no_json = os.path.splitext(os.path.basename(file_path))[0]

    with open(file_path, 'r', encoding='utf-8') as f:
        news_data = json.load(f)

    news_data = news_preprocessing(news_data)
    print(f"{file} : 뉴스 전처리 완료")

    
    kiwi = Kiwi()
    counter = Counter()
    tokens_list = []
    tags = {"NNG", "NNP", "VV", "VA", "SL"}

    stopwords = Stopwords()
    s_words = {('귀농', 'NNG'), ('이번', 'NNG'), ('기자', 'NNG'), ('만들', 'VV'), ('가능', 'NNG'),
                ('마련', 'NNG'), ('지나', 'VV'), ('밝히', 'VV'), ('보이', 'VV'), ('이어지', 'VV'), 
                ('열리', 'VV')}
    stopwords.add(s_words)

    # mininterval 업데이트 간격 
    for news in tqdm(news_data, total=len(news_data), mininterval=1):
        if len(news) < 10:
            continue

        # 불용어 제거, 특정 품사이면서 길이가 2 이상인 단어만 추출
        tokens = []
        for token in kiwi.tokenize(news, normalize_coda=True, stopwords=stopwords):
            if token.tag in tags and len(token.form) > 1:
                tokens.append(token.form) # 토큰 태그 찾기 (token.form, token.tag) 튜플로 확인 
        

        if len(tokens) >= 10:
            tokens_list.append(tokens)
            counter.update(tokens)
        

    print(f"{file} : 키워드 분석 완료")
    # 상위 n개 단어 빈도 출력
    top_num = 50
    # for word, freq in counter.most_common(top_num): print(word, freq)

    # 토픽 모델링, 행렬을 토픽갯수로 나누어 표현 
    topic_modeling(counter, tokens_list, file_no_json)
    print(f"{file} : 토픽 모델링 완료")

    
    # 상위 top_num개 막대그래프 시각화
    top_words = counter.most_common(top_num)
    words = [w for w, c in top_words]
    counts = [c for w, c in top_words]

    plt.figure(figsize=(10, max(6, top_num * 0.35)))  
    plt.barh(words[::-1], counts[::-1])  
    plt.xlabel("Count")
    plt.ylabel("word")
    plt.title(f"Top {top_num} words")
    plt.tight_layout()

    # 확장자명 json -> png 로 변경 ( 시각화 .png 파일 저장 위치용도)
    file_no_json = f"{file_no_json}.png"
    png_path = os.path.join("news_crawl/keyword_result", file_no_json)
    plt.savefig(png_path)
    #plt.show()

    return 0;

if __name__ == "__main__":
    # 크롤링 결과 폴더 crawl_result 내의 모든 json 파일을 분석
    for file in all_json:
        keyword_separation(file)
        print(f"{file} : 완료")
        print()