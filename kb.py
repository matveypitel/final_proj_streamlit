# Поиск по базе знаний проекта (только чтение). Базу собирает build_index.py
import chromadb
from dotenv import load_dotenv
from openai import OpenAI

from config import CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL, MAX_DISTANCE

load_dotenv()


openai_client = OpenAI()


def get_embedding(text):
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(COLLECTION_NAME)


def search(query, n_results=3, max_distance=MAX_DISTANCE):
    """Возвращает список найденных фрагментов: текст, документ, страница."""
    collection = get_collection()
    found = collection.query(query_embeddings=[get_embedding(query)], n_results=n_results)
    fragments = []
    for text, meta, distance in zip(
        found["documents"][0], found["metadatas"][0], found["distances"][0]
    ):
        if distance <= max_distance:
            fragments.append({"text": text, "source": meta["source"], "page": meta["page"]})
    return fragments
