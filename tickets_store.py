# Хранилище заявок: функции модуля 1 (уроки 4–6) и create_ticket_once (уроки 32–33)
import json

from config import TICKETS_FILE

CATEGORY_KEYWORDS = {
    "Оплата": ["оплат", "деньги", "чек", "списал"],
    "Доступ": ["пароль", "войти", "вход", "логин"],
    "Обучение": ["видео", "урок", "задани"],
}
DEFAULT_CATEGORY = "Другое"


def load_tickets(path=TICKETS_FILE):
    """Читает список заявок из JSON. Если файла нет, возвращает []."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_tickets(tickets, path=TICKETS_FILE):
    """Сохраняет список заявок в JSON."""
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(tickets, file, ensure_ascii=False, indent=2)


def detect_category(text):
    """Возвращает категорию заявки по ключевым словам."""
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for word in keywords:
            if word in text_lower:
                return category
    return DEFAULT_CATEGORY


def next_id(tickets):
    """Возвращает номер для новой заявки: максимум плюс один."""
    max_id = 0
    for ticket in tickets:
        if ticket["id"] > max_id:
            max_id = ticket["id"]
    return max_id + 1


def find_ticket(tickets, ticket_id):
    """Возвращает заявку с нужным номером или None."""
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket
    return None


def create_ticket_once(draft, path=TICKETS_FILE):
    """Создаёт заявку из черновика. Повторный вызов с тем же draft_id
    возвращает уже созданную заявку и ничего не дописывает."""
    tickets = load_tickets(path)
    for ticket in tickets:
        if ticket.get("draft_id") == draft["draft_id"]:
            return ticket
    ticket = {
        "id": next_id(tickets),
        "draft_id": draft["draft_id"],
        "author": draft["author"],
        "author_id": draft["author_id"],  # урок 33: чья это заявка
        "text": draft["text"],
        "category": draft["category"],
        "status": "new",
    }
    tickets.append(ticket)
    save_tickets(tickets, path)
    return ticket
