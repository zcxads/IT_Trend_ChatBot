from langchain_community.document_loaders import JSONLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


DIR_PATH = '/IT_trend_chatbot/data'

def directory_loader(directory_path):
    loader = DirectoryLoader(path=directory_path, glob='*.json')
    data = loader.load()

    return data

def document_concat(data):
    docs = []

    for i in range(len(data)):
        loader = JSONLoader(
            file_path=data[i].metadata['source'],
            jq_schema=".[].Content",
            text_content=False,
        )
        docs.extend(loader.load())

    return docs

def document_split(docs):
    docs_split = []
    split_size = len(docs) // 10

    for i in range(10):
        start_idx = i * split_size
        end_idx = (i + 1) * split_size if i < 9 else len(docs)
        docs_split.append(docs[start_idx:end_idx])

    return docs_split

def text_split(docs_split):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    chunk_split = []

    for docs in docs_split:
        chunk_split.append(text_splitter.split_documents(docs))

    return chunk_split

def save_vectorstore(docs, folder_path, index_name, embeddings):
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(folder_path=folder_path, index_name=index_name)


data = directory_loader(DIR_PATH)
docs = document_concat(data)
docs_split = document_split(docs)
chunk_split = text_split(docs_split)

embeddings = HuggingFaceEmbeddings(
    model_name='BAAI/bge-m3',
    model_kwargs={'device':'cpu'},
    encode_kwargs={'normalize_embeddings':True},
)

for i in range(10):
    folder_path = f'faiss_db{i+1}'
    index_name = f'faiss_index{i+1}'
    save_vectorstore(chunk_split[i], folder_path, index_name, embeddings)

db = FAISS.load_local(
    folder_path="faiss_db1",
    index_name="faiss_index1",
    embeddings=embeddings,
    allow_dangerous_deserialization=True,
)

for i in range(2, 11):
    db_to_merge = FAISS.load_local(
        folder_path=f"faiss_db{i}",
        index_name=f"faiss_index{i}",
        embeddings=embeddings,
        allow_dangerous_deserialization=True,
    )
    db.merge_from(db_to_merge)

db.save_local(folder_path='faiss_db')
