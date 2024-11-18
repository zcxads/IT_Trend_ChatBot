# Langchain을 활용한 IT 트렌드 챗봇 개발
- news articles data RAG ChatBot
- Version1 완료 후 Version2 branch 생성해서 업그레이드 작업 진행

## ChatBot - Version1 Streamlit App link
- https://it-trend-chatbot-app-v1.streamlit.app

## 문제 정의
- 2020년부터 2024년 현재까지의 AI 기사 데이터를 이용하여 최신 IT 트렌드 파악
- RAG, 프롬프트 엔지니어링을 활용한 LLM 기반 챗봇 구현

## Directory Structure
```
├── IT_trend_chatbot_app_v1.py
├── README.md
├── crawler
│   ├── AI_times_article.py
│   ├── AI_times_new_upload.py
│   ├── Aritificial_article.py
│   └── Artificial_new_upload.py
├── data
│   ├── AI_times_articles_20241006.json
│   └── Artificial_articles_20241006.json
├── faiss_db
│   ├── index.faiss
│   └── index.pkl
├── requirements.txt
└── vector_db.py
```

## Getting Started
- 가상환경 생성 : `python3 -m venv .venv`
- 가상환경 활성화 : `source .venv/bin/activate`
- 패키지 설치 : `pip install -r requirements.txt`
- streamlit 실행 : `streamlit run IT_trend_chatbot_app_v1.py`
