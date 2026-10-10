# Настройки финального проекта: всё, что меняют без правки логики.
# Секреты (ключи, пароль) здесь НЕ храним — они в .env и .streamlit/secrets.toml.
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

MODEL_NAME = os.getenv("AGENT_MODEL", "anthropic:claude-haiku-4-5")
RECURSION_LIMIT = 10          # шагов агента на один вопрос
MAX_MESSAGES = 20             # сообщений пользователя за сессию
MAX_TEXT_LENGTH = 500         # длина текста заявки

TICKETS_FILE = BASE_DIR / "data" / "tickets.json"
LOG_FILE = BASE_DIR / "data" / "app_log.txt"
DOCS_DIR = BASE_DIR / "docs"
CHROMA_DIR = BASE_DIR / "chroma_db"

COLLECTION_NAME = "rules"
EMBEDDING_MODEL = "text-embedding-3-small"
MAX_DISTANCE = 0.6            # порог из урока 16 — поставьте своё значение
