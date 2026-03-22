# src/application/workflows/state.py
import operator
from typing import Annotated, List, Optional, TypedDict
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class ChatState(TypedDict):
    # ── Входные данные ──
    user_query: str
    # retrieved_documents: List[dict]  # Общий список для гибрида
    # sql_documents: List[dict]        # Только SQL результаты
    # vector_documents: List[dict]     # Только векторные
    chat_id: int | None

    # ── История сообщений ──
    messages: Annotated[list[BaseMessage], add_messages]

    # ── Результаты агентов ──
    is_relevant: bool
    moderation_reason: str
    intent: str                                  # "rag" | "sql"

    retrieved_documents: Annotated[list[dict], operator.add]  # накопление
    sql_query: str                               # для логирования/дебага

    # ── Финальный ответ ──
    final_answer: str