import requests
from bs4 import BeautifulSoup as bs
import json
import time
from datetime import datetime
import re

def clean_text(text):
    """공백 및 특수 문자 제거 및 \n, \t를 공백으로 변환하고 백슬래시(\) 제거"""
    return re.sub(r'[\\\n\r\t""]', ' ', text).replace('\xa0', ' ').strip()

data = []
today = datetime.now().strftime("%Y%m%d")  # 오늘 날짜를 YYYYMMDD 형식으로 저장

# 2020.01.01~2024.10.05
for i in range(163940, 163952):
    try:
        url = f"https://www.aitimes.com/news/articleView.html?idxno={i}"
        res = requests.get(url)
        res.raise_for_status()  # 요청 실패 시 예외 발생

        soup = bs(res.text, 'lxml')

        # 제목 추출
        title_element = soup.select_one("#articleViewCon > article > header > h3")
        title = title_element.text.strip() if title_element else 'No title'

        # 기자명 추출
        reporter_element = soup.select_one("#articleViewCon > article > header > div.info-group > article:nth-child(1) > ul > li:nth-child(1)")
        if reporter_element:
            reporter_text = reporter_element.get_text(strip=True)
            reporter_name = reporter_text.replace('기자명', '').replace('기자', '').strip()
        else:
            reporter_name = 'No reporter'

        # 날짜 추출
        date_element = soup.select_one("#articleViewCon > article > header > div.info-group > article:nth-child(1) > ul > li:nth-child(2)")
        if date_element:
            date_text = date_element.get_text(strip=True)
            date_match = re.search(r'\d{4}\.\d{2}\.\d{2}', date_text)
            date_only = date_match.group(0) if date_match else None
        else:
            date_only = 'None'

        # 요약 추출
        summary_element = soup.select_one("#anchorTop > h4")
        summary_text = summary_element.text.strip() if summary_element else 'No summary'

        # 본문 추출 및 모든 문단을 하나의 문자열로 결합
        content_div = soup.select_one("#article-view-content-div")
        if content_div:
            paragraphs = content_div.find_all('p')
            combined_content = " ".join([clean_text(p.get_text()) for p in paragraphs if clean_text(p.get_text())])
        else:
            combined_content = 'No content'

        # 데이터를 리스트에 추가 (news 및 URL 컬럼 추가)
        data.append({
            'News': "AI타임스",  # news 컬럼 추가
            'ID': i,
            'Title': title,
            'Reporter': reporter_name,
            'Date': date_only,
            'Summary': summary_text,  # Summary를 추가
            'Content': combined_content,  # 모든 문단을 하나로 결합하여 저장
            'URL': url  # URL 추가
        })

        # time.sleep(0.1)  # 요청 사이에 0.1초 대기

    except requests.exceptions.HTTPError as e:
        print(f"Failed to fetch data for ID {i}: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# 파일 경로 및 이름 설정
file_path = f"/home/ubuntu/test/geon/crawler/AI_times_articles_{today}.json"

# JSON 파일로 데이터 저장
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"All articles have been processed and saved in {file_path}.")
