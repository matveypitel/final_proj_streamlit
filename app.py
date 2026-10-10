# Финальный проект: веб-помощник поддержки учебного сервиса
# Запуск из папки ai-course: streamlit run final_project/app.py
import streamlit as st

from agent_core import build_agent, run_agent
from config import MAX_MESSAGES
from security import write_log
from tickets_store import create_ticket_once

st.set_page_config(page_title="Помощник поддержки", page_icon="💬")
st.title("Помощник поддержки")

USERS = {"anna": "Анна", "boris": "Борис"}   # учебные пользователи


# ---------- Вход (готов) ----------
def check_login():
    if st.session_state.get("user_id"):
        return True
    with st.form("login"):
        login = st.selectbox("Пользователь", list(USERS), format_func=USERS.get)
        password = st.text_input("Пароль", type="password")
        if st.form_submit_button("Войти"):
            if password == st.secrets.get("APP_PASSWORD"):
                st.session_state.user_id = login
                st.session_state.user_name = USERS[login]
                st.rerun()
            st.error("Неверный пароль")
    return False


if not check_login():
    st.stop()


@st.cache_resource
def get_agent():
    return build_agent()


# ---------- История диалога (TODO 1) ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_ticket" not in st.session_state:
    st.session_state.pending_ticket = None


# ---------- Источники (TODO 3) ----------
def show_sources(sources):
    with st.expander("Источники"):
        for source in sources:
            st.write(f"{source['source']}, стр. {source['page']}")


# ---------- Кнопки карточки заявки (TODO 4) ----------
def confirm_ticket():
    draft = st.session_state.pending_ticket
    st.session_state.pending_ticket = None   # второе нажатие найдёт пустой черновик
    if draft is None:
        return
    ticket = create_ticket_once(draft)
    st.session_state.messages.append(
        {"role": "assistant", "content": f"Заявка №{ticket['id']} создана."})


def cancel_ticket():
    st.session_state.pending_ticket = None
    st.session_state.messages.append({"role": "assistant", "content": "Заявка не создана."})


# ---------- Боковая панель (готова) ----------
with st.sidebar:
    st.write(f"Вы вошли как **{st.session_state.user_name}**")
    if st.button("Новый диалог"):
        st.session_state.messages = []
        st.session_state.pending_ticket = None
        st.rerun()

# ---------- Вывод истории (TODO 1) ----------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            show_sources(message["sources"])

# ---------- Лимит сообщений (готов) ----------
user_count = sum(1 for m in st.session_state.get("messages", []) if m["role"] == "user")
prompt = st.chat_input("Ваш вопрос", disabled=user_count >= MAX_MESSAGES)
if user_count >= MAX_MESSAGES:
    st.info("Лимит сообщений в этом диалоге исчерпан. Начните новый диалог.")

# ---------- Вопрос и ответ (TODO 2) ----------
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    with st.chat_message("assistant"):
        with st.spinner("Ищу ответ…"):
            try:
                report = run_agent(get_agent(), history,
                                   st.session_state.user_id, st.session_state.user_name)
            except Exception:  # последний рубеж: сеть, ключ, лимиты провайдера
                report = {"answer": "", "error": "Сервис временно недоступен.",
                          "tools": [], "sources": [], "draft": None}
        answer = report["error"] or report["answer"]
        st.markdown(answer)
        if report["sources"]:
            show_sources(report["sources"])
    write_log(st.session_state.user_id, prompt, report["tools"], report["error"])
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": report["sources"]})
    if report["draft"]:
        st.session_state.pending_ticket = report["draft"]
    if user_count + 1 >= MAX_MESSAGES:
        st.rerun()  # сразу погасить поле ввода: лимит исчерпан

# ---------- Карточка заявки (TODO 4) ----------
draft = st.session_state.pending_ticket
if draft:
    with st.container(border=True):
        st.markdown(f"**Новая заявка** · {draft['category']}")
        st.write(draft["text"])
        st.caption(f"Автор: {draft['author']}")
        col1, col2 = st.columns(2)
        col1.button("Создать", on_click=confirm_ticket, type="primary")
        col2.button("Отменить", on_click=cancel_ticket)
