# Защита приложения (урок 33): контекст пользователя, права, маскирование, журнал
import re
from dataclasses import dataclass
from datetime import datetime

from config import LOG_FILE


@dataclass
class UserContext:
    """Кто сейчас работает с приложением. Заполняет приложение, а не модель."""
    user_id: str
    user_name: str


def can_view_ticket(ticket, user_id):
    """Пользователь видит только свои заявки."""
    return ticket is not None and ticket.get("author_id") == user_id


EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"\+?\d[\d\s()-]{8,}\d")


def mask_pii(text):
    """Заменяет email и телефон на метки перед отправкой в модель и в журнал."""
    text = EMAIL.sub("[email]", text)
    return PHONE.sub("[телефон]", text)


def write_log(user_id, question, tools, error):
    """Журнал без личных данных и ключей: кто, длина вопроса, инструменты, ошибка."""
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} | {user_id} | "
                   f"вопрос {len(question)} симв. | {tools} | {error or 'ok'}\n")


if __name__ == "__main__":
    print(mask_pii("Пишите на anna.k@mail.ru или +7 (912) 345-67-89, заказ 12345"))
