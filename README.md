# 최신 AI 기사를 참조한 챗봇 프로젝트
- news articles data RAG ChatBot
- Version1 완료 후 Version2 branch 생성해서 업그레이드 작업 진행

## ChatBot - Version1 Streamlit App link
- https://it-trend-chatbot-app-v1.streamlit.app

## 문제 정의
- 2020년부터 2024년 현재까지의 AI 기사 데이터를 이용하여 최신 트렌드 파악
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

## Description
- `data/`: 학습데이터/평가데이터 csv 파일 
- `configs/`: accelerate 및 fsdp config 파일
- `utils.py`: 학습 및 추론하는데 필요한 함수들 정리한 python script
- `train.py`: LLM 모델 학습하는 python script
- `inference.py`: LLM 모델 추론하는 python script
- `run.sh`: LLM 모델 config 값 설정하여 train.py 실행하는 shell script
- `sample_submission.csv`: 제출 csv 파일 예시
 

## Getting Started
- 가상환경 생성 : `python3 -m venv .venv`
- 가상환경 활성화 : `source .venv/bin/activate`
- 패키지 설치 : `pip install -r requirements.txt`
- streamlit 실행 : `streamlit run IT_trend_chatbot_app_v1.py`
