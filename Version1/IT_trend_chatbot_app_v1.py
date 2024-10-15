import streamlit as st
import os
import uuid # 고유 ID 생성을 위한 라이브러리
from pymongo import MongoClient
from langchain_core.messages import HumanMessage, AIMessage, ChatMessage
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_community.chat_message_histories import ChatMessageHistory



########################################## 경로 지정 ##################################################
#VECTOR_STORE_PATH = "/IT_trend_chatbot/faiss_db" # 깃허브 경로 연결
VECTOR_STORE_PATH = "./faiss_db"
#VECTOR_STORE_PATH = 'Version1/faiss_db'
CACHE_DIR = ".cache"
EMBEDDINGS_DIR = ".cache/embeddings"


# MongoDB 클라이언트 설정
client = MongoClient("mongodb://test:test@43.203.128.206:27017/", serverSelectionTimeoutMS=5000)  # 'test' 사용자 인증 정보 사용
db = client["admin"]  # 'admin' 데이터베이스 사용
messages_collection = db["messages"]  # 'messages' 컬렉션 사용


# Sidebar
with st.sidebar:
    clear_btn = st.button("대화 초기화")
    selected_model = st.selectbox("LLM 선택", ["gemma2:2b", "gemma2"], index=0)
    session_id = st.text_input("세션 ID를 입력하세요.", "abc123")

    # 사용자 ID 입력란에 기본값을 제거하고 placeholder만 유지
    session_id = st.text_input(
        "사용자 ID를 입력하세요.", 
        value=st.session_state.get("user_id", ""),  # 세션 상태의 user_id를 기본 값으로 사용
        placeholder="여기에 사용자ID를 입력하세요"
    )



# 캐시 & 임베딩 디렉토리 생성
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

################################### 세션 초기화 ######################################
# session_state : 웹 앱의 상태를 저장하고 관리하는 방법 = 사용자 세션 동안 데이터를 유지
    # dict와 유사하게 작동, 키-값 쌍 저장
    # streamlit은 기본적으로 실행할 때 마다, 전체 페이지 다시 실행하는데 세션을 통해 데이터 유지가능

# messages : 사용자와 챗봇 간의 대화 기록
if "messages" not in st.session_state:
    st.session_state.messages = []
# RAG chain -> 이후 create_rag_chain() 함수를 통해 실제 chain객체로 초기화
if "chain" not in st.session_state:
    st.session_state.chain = None
# store : 여러 세션의 대화 기록을 관리하는 dict
    # 각 세션 ID를 키로 사용하여 해당 세션의 ChatMessageHistory객체 저장 -> 여러 사용자(대화) 세션 관리
if "store" not in st.session_state:
    st.session_state.store = {}

if "user_id" not in st.session_state:
    st.session_state.user_id = None  # 사용자 고유 ID
if "gender" not in st.session_state:
    st.session_state.gender = None
if "age" not in st.session_state:
    st.session_state.age = None


# 각 세션에 대한 대화기록 관리
def get_session_history(session_id):
    if session_id not in st.session_state.store:
        st.session_state.store[session_id] = ChatMessageHistory()
    return st.session_state.store[session_id]

################################# 임베딩 정의 ###########################################

@st.cache_resource
def get_embeddings():
    return HuggingFaceBgeEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"}, # cuda or cpu
        encode_kwargs={"normalize_embeddings": True}
    )

# 임베딩이 다양한 입력 형식을 처리하도록 함 : 임베딩이 항상 문자열 입력을 받도록 보장
def safe_embed_query(embedding_function, text):
    if isinstance(text, dict) and "question" in text:
        text = text["question"]
    if not isinstance(text, str):
        text = str(text)
    return embedding_function.embed_query(text)

############################### 벡터스토어 로드 ############################################

@st.cache_resource(show_spinner="벡터스토어 로드... or 생성...중입니다.")
def load_or_create_vector_store():
    embeddings = get_embeddings()
    
    if os.path.exists(VECTOR_STORE_PATH):
        vectorstore = FAISS.load_local(VECTOR_STORE_PATH, embeddings, allow_dangerous_deserialization=True)
    else:
        pass
    
    vectorstore._embed_query = lambda text: safe_embed_query(embeddings, text)
    
    return vectorstore

################################################### 체인생성 ####################################################

def create_rag_chain():
    vectorstore = load_or_create_vector_store()
    retriever = vectorstore.as_retriever()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 Question-Answering 챗봇입니다. 주어진 질문에 대한 답변을 제공해주세요."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", """
주어진 정보를 바탕으로 사용자의 질문에 답변해주세요. 다음 지침을 따라주세요:

1. 한국어로 답변하세요.
2. 간결하고 명확하게 답변하세요.
3. 확실하지 않은 정보는 추측하지 말고 모른다고 하세요.
4. 답변은 3-4문장을 넘지 않도록 해주세요.

컨텍스트: {context}

질문: {question}

답변:
""")
    ])
    
    llm = ChatOllama(model=selected_model, temperature=0)
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    chain = (
        RunnablePassthrough.assign(
            context=retriever | format_docs
        )
        | prompt
        | llm
        | StrOutputParser()
    )
    # RunnableWithMessageHistory : 기존 chain에 대화기록관리 기능 추가
    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history",
    )
    
    return chain_with_history

############################################ 스트림릿 ##############################################

# CSS를 사용하여 selectbox에 커서 스타일 추가
st.markdown("""
    <style>
        .stSelectbox > div > div {
            cursor: pointer;  /* 마우스를 올리면 손 모양으로 변경 */
        }
    </style>
""", unsafe_allow_html=True)



# Streamlit UI
st.title("IT 트렌드 챗봇 💬")

if st.session_state.chain is None:
    st.session_state.chain = create_rag_chain()

# 사용자 정보 입력 단계
if st.session_state.gender is None or st.session_state.age is None:
    st.header("사용자 정보를 입력해주세요")
    with st.form("user_info_form"):
        gender = st.selectbox("성별을 선택하세요", ["남성", "여성", "기타"])
        age = st.selectbox("나이를 입력하세요", list(range(1, 101)))
        submitted = st.form_submit_button("확인")
        if submitted:
            user_id = str(uuid.uuid4())  # 고유 사용자 ID 생성
            st.session_state.user_id = user_id
            st.session_state.gender = gender
            st.session_state.age = age
            # 사용자 정보를 MongoDB에 저장
            user_info = {
                "user_id": user_id,
                "gender": st.session_state.gender,
                "age": st.session_state.age
            }
            messages_collection.insert_one({"role": "system", "content": f"User info: {user_info}"})
            st.success(f"정보가 저장되었습니다. 사용자 ID는 {user_id}입니다.")
    
    # st.form() 외부로 버튼 이동
    if st.session_state.user_id and st.button("사용자 ID 자동입력"):
        st.session_state["session_id"] = st.session_state.user_id
        st.success(f"사용자 ID가 입력되었습니다: {st.session_state['session_id']}")

else:
    # 대화기록 초기화 및 새로운 세션 할당
    if clear_btn:
        st.session_state.messages = []
        st.session_state.store[st.session_state.user_id] = ChatMessageHistory()
        st.session_state.gender = None
        st.session_state.age = None
        st.session_state.user_id = None
        st.session_state["page_refresh"] = True
    
    # 대화기록 ui 생성
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input : 사용자 입력 받기
    if user_input := st.chat_input("궁금한 내용을 물어보세요!"):
        # 사용자 입력을 MongoDB에 저장
        user_message = {
            "role": "user",
            "content": user_input,
            "user_id": st.session_state.user_id
        }
        messages_collection.insert_one(user_message)  # 사용자 메시지 저장
        st.session_state.messages.append(user_message)
        with st.chat_message("user"):
            st.markdown(user_input)

        # 챗봇 응답 생성
        with st.chat_message("AI_chatbot"):
            message_placeholder = st.empty()
            full_response = ""
            try:
                for chunk in st.session_state.chain.stream(
                    {"question": user_input},
                    config={"configurable": {"session_id": st.session_state.user_id}}
                ):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                full_response = "죄송합니다. 답변 생성 중 오류가 발생했습니다."

            # 챗봇 응답을 MongoDB에 저장
            assistant_message = {
                "role": "AI_chatbot",
                "content": full_response,
                "user_id": st.session_state.user_id
            }
            messages_collection.insert_one(assistant_message)  # 챗봇 응답 저장
            st.session_state.messages.append(assistant_message)
            message_placeholder.markdown(full_response)

  

    # 대화 기록 초기화 버튼
    if st.button("대화 기록 초기화"):
        # 세션에서 메시지 목록을 비워 화면에서 메시지를 삭제
        st.session_state.messages = []
        # 페이지를 재실행하여 변경 사항을 적용
        st.rerun()



# 추가된 부분: IT 트렌드 정보 표시
st.sidebar.markdown("## 최신 IT 트렌드 정보")
st.sidebar.markdown("1. AI 기술의 발전과 응용")
st.sidebar.markdown("2. 윤리적 AI 개발")
st.sidebar.markdown("3. 엔터프라이즈 IT와 AI의 통합")
st.sidebar.markdown("4. 멀티모달 AI의 발전")
st.sidebar.markdown("5. 생성형 AI의 비즈니스 적용")

# 추가된 부분: 유용한 링크
st.sidebar.markdown("## 유용한 링크")
st.sidebar.markdown("[2024년 AI 트렌드 전망](https://m.post.naver.com/viewer/postView.naver?volumeNo=37445396&memberNo=33037825)")
st.sidebar.markdown("[IBM의 2024 AI 트렌드 예측](https://aiheroes.ai/community/163)")
st.sidebar.markdown("[마이크로소프트의 2024년 AI 트렌드](https://www.clunix.com/insight/it_trends.php?boardid=ittrend&mode=view&idx=819)")
st.sidebar.markdown("[AI타임스](https://www.aitimes.com/)")
st.sidebar.markdown("[인공지능신문](https://www.aitimes.kr/)")