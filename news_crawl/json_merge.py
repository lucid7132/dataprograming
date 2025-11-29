import os
import json
from glob import glob

# 크롤링 결과 폴더 crawl_result 내의 filename_YYYY.json 을 합치는 코드입니다!

def merge_json(filename:str):
    json_path =  "news_crawl/crawl_result"
    output_file = f"{filename}.json"

    json_files = sorted(glob(os.path.join(json_path, f"{filename}_*.json")))

    merged_data = []

    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                merged_data.extend(data)
            else:
                print("리스트 타입이 아닙니다.")
    
    with open(os.path.join(json_path, output_file), "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=4)

    print(f"{output_file} 생성완료")

if __name__ == "__main__":

    try:
        print("합치려는 filename_YYYY.json 에서 filename 을 입력해주세요")
        filename= input()
        merge_json(filename)
    except Exception as e:
        print(f"오류발생 : {e}")