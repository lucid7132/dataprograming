import os
import json
from tqdm import tqdm
import matplotlib.pyplot as plt

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# from keyword_separation import news_preprocessing 홀로 실행시 필요함 198줄 연계

# 감성 분석 모델 초기화 
sentiment_tokenizer = None
sentiment_model = None
device = None

def initialize_sentiment_model():
    # 감성 분석 모델 초기화
    global sentiment_tokenizer, sentiment_model, device
    
    # GPU 사용 가능하면 GPU, 아니면 CPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 실제 감성 분석용으로 fine-tuned된 모델 사용
    model_name = "matthewburke/korean_sentiment"
    
    try:
        sentiment_tokenizer = AutoTokenizer.from_pretrained(model_name)
        sentiment_model = AutoModelForSequenceClassification.from_pretrained(model_name)
        sentiment_model.to(device)
        sentiment_model.eval()
        print("감성 분석 모델 로드 완료")
        print(f"사용 모델: {model_name}")
    except Exception as e:
        print(f"모델 로드 실패: {e}")
        print("대안: 간단한 키워드 기반 감성 분석을 사용합니다.")
        return False
    
    return True

def analyze_sentiment_simple(text: str) -> str:
    # 간단한 키워드 기반 감성 분석 (모델 로드 실패시 대안)
    # 뉴스 기사 키워드 (귀농 관련)
    positive_keywords = ['성공', '발전', '증가', '개선', '확대', '좋', '긍정', '상승', 
                         '활성화', '지원', '혜택', '기대', '성장', '향상', '안정',
                         '호황', '풍부', '만족', '선호', '인기', '활발', '증진',
                         '효과', '달성', '수익', '번창']
    negative_keywords = ['감소', '하락', '문제', '어려움', '부족', '위기', '악화', 
                         '실패', '폐쇄', '중단', '축소', '우려', '불안', '침체',
                         '곤란', '피해', '손실', '고령화', '빈곤', '붕괴']
    
    # 텍스트 정규화
    text_lower = text.lower()
    
    pos_count = sum(text.count(keyword) for keyword in positive_keywords)
    neg_count = sum(text.count(keyword) for keyword in negative_keywords)
    
    # 점수 차이가 있으면 그에 따라 분류
    if pos_count > neg_count + 1:  # 더 명확한 차이가 있을 때만
        return 'positive'
    elif neg_count > pos_count + 1:
        return 'negative'
    else:
        return 'neutral'

def analyze_sentiment_model(text: str) -> str:
    # 모델 기반 감성 분석
    try:
        # 텍스트가 너무 길면 앞부분만 사용 (512 토큰 제한)
        inputs = sentiment_tokenizer(
            text[:512], 
            return_tensors="pt", 
            truncation=True, 
            padding=True,
            max_length=512
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = sentiment_model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            predicted_class = torch.argmax(predictions, dim=-1).item()
            confidence = predictions[0][predicted_class].item()
        
        # matthewburke/korean_sentiment 모델의 클래스 매핑
        # 0: 부정(negative), 1: 긍정(positive)
        sentiment_map = {0: 'negative', 1: 'positive'}
        
        # confidence가 0.6 미만이면 중립으로 처리 (확신도가 낮은 경우)
        if confidence < 0.6:
            return 'neutral'
        
        return sentiment_map.get(predicted_class, 'neutral')
        
    except Exception as e:
        print(f"감성 분석 오류: {e}")
        return 'neutral'

def sentiment_analysis(news_data: list, file_no_json: str):
    # 뉴스 데이터에 대한 감성 분석 수행
    
    print(f"{file_no_json} : 감성 분석 시작")
    
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    sentiment_results = []
    
    use_model = sentiment_model is not None
    
    for article_text in tqdm(news_data, desc="감성 분석 중", mininterval=1):
        if len(article_text) < 10:
            continue
        
        # 모델 사용 여부에 따라 다른 함수 호출
        if use_model:
            sentiment = analyze_sentiment_model(article_text)
        else:
            sentiment = analyze_sentiment_simple(article_text)
        
        sentiment_counts[sentiment] += 1
        sentiment_results.append({
            'text_preview': article_text[:100],  # 처음 100자만 저장
            'sentiment': sentiment
        })
    
    # 결과 저장
    sentiment_dir = "news_crawl/sentiment_result"
    os.makedirs(sentiment_dir, exist_ok=True)
    
    # JSON 파일 결과 저장
    result_file = os.path.join(sentiment_dir, f"{file_no_json}_sentiment.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': sentiment_counts,
            'details': sentiment_results
        }, f, ensure_ascii=False, indent=2)
    
    # 시각화
    visualize_sentiment(sentiment_counts, file_no_json)
    
    print(f"{file_no_json} : 감성 분석 완료")
    print(f"  긍정: {sentiment_counts['positive']}")
    print(f"  부정: {sentiment_counts['negative']}")
    print(f"  중립: {sentiment_counts['neutral']}")
    
    return sentiment_counts

def visualize_sentiment(sentiment_counts: dict, file_no_json: str):
    # 감성 분석 결과 시각화
    
    sentiment_dir = "news_crawl/sentiment_result"
    
    # 파이 차트
    labels = ['긍정', '부정', '중립']
    sizes = [sentiment_counts['positive'], 
             sentiment_counts['negative'], 
             sentiment_counts['neutral']]
    colors = ['#90EE90', '#FFB6C1', '#D3D3D3']
    explode = (0.1, 0.1, 0)
    
    plt.figure(figsize=(10, 6))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=False, startangle=90)
    plt.axis('equal')
    plt.title(f'{file_no_json} 감성 분석 결과')
    
    pie_path = os.path.join(sentiment_dir, f"{file_no_json}_sentiment_pie.png")
    plt.savefig(pie_path)
    plt.close()
    
    # 막대 그래프
    plt.figure(figsize=(8, 6))
    plt.bar(labels, sizes, color=colors)
    plt.xlabel('감성')
    plt.ylabel('뉴스 개수')
    plt.title(f'{file_no_json} 감성 분석 결과')
    
    # 막대 위에 숫자 표시
    for i, v in enumerate(sizes):
        plt.text(i, v + max(sizes)*0.01, str(v), ha='center', va='bottom')
    
    bar_path = os.path.join(sentiment_dir, f"{file_no_json}_sentiment_bar.png")
    plt.savefig(bar_path)
    plt.close()

if __name__ == "__main__":

    # json 폴더 경로 + 파일이름 
    dir_path = "news_crawl/crawl_result"
    all_json = os.listdir(dir_path)
    file = all_json[0]
    file_path = os.path.join(dir_path, file)

    # 확장자 json 없는 파일명 저장 
    file_no_json = os.path.splitext(os.path.basename(file_path))[0]

    with open(file_path, 'r', encoding='utf-8') as f:
        news_data = json.load(f)

    # news_data = news_preprocessing(news_data)
    
    # 감성 분석 모델 초기화
    model_loaded = initialize_sentiment_model()
    if not model_loaded:
        print("키워드 기반 간단한 감성 분석을 사용합니다.")

    sentiment_analysis(news_data, file_no_json)
    