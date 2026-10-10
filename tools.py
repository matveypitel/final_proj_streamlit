# Инструменты агента (уроки 32–34): данные отделены от инструкций,
# пользователь берётся из контекста запуска, права проверяет код,
# сбой хранилища можно имитировать переменной TOOLS_DOWN=1.
import json
import os
import uuid

from langchain.tools import ToolRuntime, tool

import kb
from config import MAX_TEXT_LENGTH
from security import UserContext, can_view_ticket
from tickets_store import detect_category, find_ticket, load_tickets


def to_json(data):
    return json.dumps(data, ensure_ascii=False)


def check_service():
    """Учебная имитация сбоя хранилища: TOOLS_DOWN=1."""
    if os.getenv("TOOLS_DOWN") == "1":
        raise ConnectionError("Хранилище заявок не отвечает")


@tool(response_format="content_and_artifact", parse_docstring=True)
def search_docs(query: str):
    """Ищет ответ в правилах учебного сервиса: оплата, возврат, доступ, сертификаты.
    Не используй для статуса конкретного обращения.

    Args:
        query: короткий поисковый запрос своими словами, например «возврат денег».
    """
    fragments = kb.search(query)
    if len(fragments) == 0:
        return to_json({"found": False}), []
    parts = []
    for fragment in fragments:
        parts.append(
            f'<document source="{fragment["source"]}" page="{fragment["page"]}">\n'
            f'{fragment["text"]}\n</document>'
        )
    text = "\n".join(parts)
    sources = [{"source": f["source"], "page": f["page"]} for f in fragments]
    return text, sources


@tool(parse_docstring=True)
def get_ticket_status(ticket_id: int, runtime: ToolRuntime[UserContext]) -> str:
    """Возвращает статус обращения текущего пользователя по номеру.

    Args:
        ticket_id: номер обращения, целое число больше 0.
    """
    if ticket_id < 1:
        return to_json({"ok": False, "error": "Номер обращения должен быть больше 0"})
    try:
        check_service()
        ticket = find_ticket(load_tickets(), ticket_id)
    except (ConnectionError, OSError, json.JSONDecodeError) as error:
        return to_json({"ok": False, "error": f"Хранилище заявок недоступно: {error}"})
    # Проверка прав (TODO 7): чужая заявка выглядит как несуществующая
    if not can_view_ticket(ticket, runtime.context.user_id):
        return to_json({"ok": True, "found": False, "ticket_id": ticket_id})
    return to_json({"ok": True, "found": True, "ticket_id": ticket_id,
                    "status": ticket["status"], "category": ticket["category"]})


@tool(parse_docstring=True)
def propose_ticket(text: str, runtime: ToolRuntime[UserContext]) -> str:
    """Готовит черновик новой заявки от имени текущего пользователя. Заявку НЕ создаёт:
    пользователь подтверждает её кнопкой в интерфейсе. Вызывай, только когда
    пользователь просит создать заявку и описал проблему.

    Args:
        text: описание проблемы словами пользователя, до 500 символов.
    """
    text = text.strip()
    if text == "" or len(text) > MAX_TEXT_LENGTH:
        return to_json({"ok": False,
                        "error": "Текст заявки должен быть от 1 до 500 символов"})
    draft = {
        "draft_id": uuid.uuid4().hex,
        "author": runtime.context.user_name,
        "author_id": runtime.context.user_id,
        "text": text,
        "category": detect_category(text),
    }
    return to_json({"ok": True, "draft": draft,
                    "message": "Черновик показан пользователю. Заявка ещё НЕ создана."})


TOOLS = [search_docs, get_ticket_status, propose_ticket]
