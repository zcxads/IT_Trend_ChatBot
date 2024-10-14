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

# 파일 경로 설정
index_file_path = "/home/ubuntu/test/geon/crawler/AI_times_last_crawled_index.txt"
data = []
today = datetime.now().strftime("%Y%m%d")

# 마지막 크롤링한 index 읽기
AI_times_last_crawled_index = read_last_index(index_file_path)
if AI_times_last_crawled_index is None:
    AI_times_last_crawled_index = 163952  # 초기 값 설정

# 설정
no_content_counter = 0
max_no_content = 5
valid_last_index = AI_times_last_crawled_index

# 크롤링 범위 설정
for i in range(AI_times_last_crawled_index, AI_times_last_crawled_index + 500):  # 다음 500개 항목을 크롤링
    try:
        url = f"https://www.aitimes.com/news/articleView.html?idxno={i}"
        res = requests.get(url)
        res.raise_for_status()

        soup = bs(res.text, 'lxml')

        title_element = soup.select_one("#articleViewCon > article > header > h3")
        title = title_element.text.strip() if title_element else None

        reporter_element = soup.select_one("#articleViewCon > article > header > div.info-group > article:nth-child(1) > ul > li:nth-child(1)")
        reporter_name = reporter_element.get_text(strip=True).replace('기자명', '').replace('기자', '').strip() if reporter_element else None

        date_element = soup.select_one("#articleViewCon > article > header > div.info-group > article:nth-child(1) > ul > li:nth-child(2)")
        if date_element:
            date_text = date_element.get_text(strip=True)
            date_match = re.search(r'\d{4}\.\d{2}\.\d{2}', date_text)
            date_only = date_match.group(0) if date_match else None
        else:
            date_only = None

         # 요약 추출
        summary_element = soup.select_one("#anchorTop > h4")
        summary_text = summary_element.text.strip() if summary_element else 'No summary'

        content_div = soup.select_one("#article-view-content-div")
        combined_content = " ".join([clean_text(p.get_text()) for p in content_div.find_all('p')]) if content_div else None

        if title and reporter_name and date_only and combined_content:
            data.append({
                'News': "AI타임스",
                'ID': i,
                'Title': title,
                'Reporter': reporter_name,
                'Date': date_only,
                'Summary': summary_text,
                'Content': combined_content,
                'URL': url
            })
            no_content_counter = 0
            valid_last_index = i
        else:
            no_content_counter += 1

        if no_content_counter >= max_no_content:
            print(f"Stopping crawl after {no_content_counter} consecutive invalid articles.")
            break

    except requests.exceptions.HTTPError as e:
        print(f"Failed to fetch data for ID {i}: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# 마지막 유효한 index 저장
write_last_index(index_file_path, valid_last_index + 1)

# 데이터 파일 저장
file_path = f"/home/ubuntu/test/geon/crawler/AI_times_articles_{today}.json"
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"All articles have been processed and saved in {file_path}.")