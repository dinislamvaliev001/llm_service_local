# src/application/workflows/chat_graph.py
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.application.workflows.state import ChatState
from src.application.agents.moderation_agent import (
    moderation_node,
    should_continue_after_moderation,
)
from src.application.agents.intent_router import (
    intent_router_node,
    route_by_intent,
)
from src.application.agents.rag_agent import (
    rag_agent_node,
    should_continue_rag,
    collect_retrieved_documents,
)
from src.application.agents.sql_agent import sql_agent_node
from src.application.agents.writer_agent import blocked_node, writer_node

import logging
logger = logging.getLogger(__name__)

def route_after_sql(state: ChatState) -> str:
    """Фоллбэк на RAG если SQL вернул пустой результат."""
    results = state.get("retrieved_documents") or []
    logger.warning("ROUTE AFTER SQL: retrieved_documents count = %d", len(results))
    if results:
        return "writer"
    return "rag_agent"

def build_chat_graph():
    graph = StateGraph(ChatState)

    # ── Узлы ──
    graph.add_node("moderation", moderation_node)
    graph.add_node("blocked", blocked_node)
    graph.add_node("intent_router", intent_router_node)
    graph.add_node("rag_agent", rag_agent_node)
    graph.add_node("collect_docs", collect_retrieved_documents)
    graph.add_node("sql_agent", sql_agent_node)
    graph.add_node("writer", writer_node)

    # ── Стартовая точка ──
    graph.set_entry_point("moderation")

    # ── Рёбра ──
    graph.add_conditional_edges(
        "moderation",
        should_continue_after_moderation,
        {
            "rag_agent": "intent_router",
            "blocked": "blocked",
        },
    )

    graph.add_conditional_edges(
        "intent_router",
        route_by_intent,
        {
            "rag": "rag_agent",
            "sql": "sql_agent",
        },
    )

    # SQL → writer если есть результаты, иначе → rag_agent
    graph.add_conditional_edges(
        "sql_agent",
        route_after_sql,
        {
            "writer": "writer",
            "rag_agent": "rag_agent",
        },
    )

    graph.add_conditional_edges(
        "rag_agent",
        should_continue_rag,
        {
            # "tools": "tools",
            "writer": "collect_docs",
        },
    )
    # graph.add_edge("tools", "rag_agent")
    graph.add_edge("collect_docs", "writer")
    graph.add_edge("blocked", END)
    graph.add_edge("writer", END)

    return graph.compile()

chat_graph = build_chat_graph()