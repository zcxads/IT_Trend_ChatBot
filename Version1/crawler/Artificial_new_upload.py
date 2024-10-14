import requests
from bs4 import BeautifulSoup as bs
import json
from datetime import datetime
import os
import re

def clean_text(text):
    """공백 및 특수 문자 제거 및 \n, \t를 공백으로 변환하고 백슬래시(\) 제거"""
    return re.sub(r'[\\\n\r\t""]', ' ', text).replace('\xa0', ' ').strip()

def read_last_index(file_path):
    """마지막으로 크롤링한 index를 파일에서 읽어옵니다."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return int(file.read().strip())
    return None

def write_last_index(file_path, last_index):
    """마지막으로 크롤링한 index를 파일에 저장합니다."""
    with open(file_path, 'w') as file:
        file.write(str(last_index))

# 마지막 인덱스를 저장할 파일 경로
index_file_path = "/home/ubuntu/test/geon/crawler/artificial_last_crawled_index.txt"
data = []
today = datetime.now().strftime("%Y%m%d")

# 1. 이전에 저장된 마지막 index 읽기
artificial_last_crawled_index = read_last_index(index_file_path)

# 2. 만약 저장된 index가 없으면, 기본값 설정 (예: 32369)
if artificial_last_crawled_index is None:
    artificial_last_crawled_index = 32369

# 5번 연속으로 기사가 없으면 멈추도록 설정
no_content_counter = 0
max_no_content = 5
valid_last_index = artificial_last_crawled_index  # 유효한 마지막 기사의 index

# 3. 배치에서 사용할 range 설정 (기본적으로 마지막 index부터 시작)
for i in range(artificial_last_crawled_index, artificial_last_crawled_index + 500):  # 여기서 500은 한 번에 처리할 기사의 수
    try:
        url = f"https://www.aitimes.kr/news/articleView.html?idxno={i}"
        res = requests.get(url)
        res.raise_for_status()

        soup = bs(res.text, 'lxml')

        # 제목 추출
        title_element = soup.select_one("#article-view > div > header > h3")
        title = title_element.text.strip() if title_element else None

        # 기자명 추출
        reporter_element = soup.select_one("#article-view > div > header > div > article:nth-child(1) > ul > li:nth-child(1)")
        reporter_name = clean_text(reporter_element.get_text()).replace('기자명', '').replace('기자', '').strip() if reporter_element else None

        # 날짜 추출 (YYYY.MM.DD 형식)
        date_element = soup.select_one("#article-view > div > header > div > article:nth-child(1) > ul > li:nth-child(2)")
        date_only = date_element.get_text(strip=True).split()[1] if date_element else None

        # 요약 추출
        summary_element = soup.select_one("#snsAnchor > div > h4")
        summary_text = summary_element.text.strip() if summary_element else 'No summary'

        # 본문 추출
        content_div = soup.select_one("#article-view-content-div")
        combined_content = " ".join([clean_text(p.get_text()) for p in content_div.find_all('p')]) if content_div else None

        # 모든 필드가 유효한 경우에만 데이터를 추가
        if title and reporter_name and date_only and combined_content:
            data.append({
                'News': "인공지능신문",
                'ID': i,
                'Title': title,
                'Reporter': reporter_name,
                'Date': date_only,
                'Summary': summary_text,
                'Content': combined_content,
                'URL': url
            })
            no_content_counter = 0
            valid_last_index = i  # 유효한 기사의 index로 업데이트
        else:
            no_content_counter += 1

        # 5개 연속으로 유효하지 않은 기사면 크롤링 종료
        if no_content_counter >= max_no_content:
            print(f"Stopping crawl after {no_content_counter} consecutive invalid articles.")
            break

    except requests.exceptions.HTTPError as e:
        print(f"Failed to fetch data for ID {i}: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# 4. 마지막으로 처리한 유효한 index 저장
write_last_index(index_file_path, valid_last_index + 1)  # 다음 크롤링은 유효한 마지막 기사 +1 부터 시작

# 파일 경로 및 이름 설정
file_path = f"/home/ubuntu/test/geon/crawler/Artificial_articles_{today}.json"

# JSON 파일로 데이터 저장
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"All articles have been processed and saved in {file_path}.")
