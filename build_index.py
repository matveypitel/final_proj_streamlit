# Собирает базу знаний проекта из папки docs (по шагам модуля 3: загрузка, фрагменты, эмбеддинги).
# Запуск из папки ai-course: python final_project/build_index.py
# Поменяли документы — запустите снова: upsert перезапишет фрагменты с теми же id.
import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

from config import CHROMA_DIR, COLLECTION_NAME, DOCS_DIR, EMBEDDING_MODEL

load_dotenv()
CHUNK_SIZE = 500   # символов во фрагменте
OVERLAP = 100      # перекрытие соседних фрагментов


def clean(text):
    return " ".join(text.split())


def load_documents(folder):
    """Страницы всех PDF и TXT из папки: source, page, text."""
    pages = []
    for path in sorted(folder.glob("*")):
        if path.suffix == ".txt":
            pages.append({"source": path.name, "page": 1,
                          "text": clean(path.read_text(encoding="utf-8"))})
        elif path.suffix == ".pdf":
            for number, page in enumerate(PdfReader(path).pages, start=1):
                text = clean(page.extract_text() or "")
                if text == "":
                    print(f"{path.name}, стр. {number}: нет текста (скан?), пропускаю")
                    continue
                pages.append({"source": path.name, "page": number, "text": text})
    return pages


def chunk_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    """Режет текст на фрагменты до size символов по границам слов, с перекрытием."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            space = text.rfind(" ", start, end)
            if space > start:
                end = space
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
        space = text.find(" ", start, end)
        if space != -1:
            start = space + 1
    return chunks


def main():
    pages = load_documents(DOCS_DIR)
    if len(pages) == 0:
        print(f"В папке {DOCS_DIR} нет документов. Скопируйте туда файлы из module3/docs.")
        return
    ids, texts, metadatas = [], [], []
    for page in pages:
        for number, chunk in enumerate(chunk_text(page["text"]), start=1):
            ids.append(f"{page['source']}-p{page['page']}-c{number}")
            texts.append(chunk)
            metadatas.append({"source": page["source"], "page": page["page"]})

    response = OpenAI().embeddings.create(model=EMBEDDING_MODEL, input=texts)
    embeddings = [item.embedding for item in response.data]

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        COLLECTION_NAME, configuration={"hnsw": {"space": "cosine"}})
    collection.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
    print(f"Страниц: {len(pages)}, фрагментов в базе: {collection.count()}")


if __name__ == "__main__":
    main()
