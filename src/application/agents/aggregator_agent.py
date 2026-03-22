# src/application/agents/aggregator_agent.py
from src.application.workflows.state import ChatState

# def aggregator_node(state: ChatState) -> dict:
#     rag_docs = state.get("rag_documents", [])
#     sql_docs = state.get("sql_documents", [])

#     return {
#         "retrieved_documents": rag_docs + sql_docs
#     }

def aggregator_node(state: ChatState) -> dict:
    rag_docs = state.get("rag_documents", [])
    sql_docs = state.get("sql_documents", [])

    combined = rag_docs + sql_docs

    # сортировка по score
    combined.sort(key=lambda x: x.get("score", 0), reverse=True)

    # threshold + top-k
    filtered = [doc for doc in combined if doc.get("score", 0) >= 0.6][:10]

    return {
        "retrieved_documents": filtered
    }