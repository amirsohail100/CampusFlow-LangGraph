"""
StatePipeline.py
-----------------
Defines the shared graph state that flows through every node of the
College Assistant agent (classifier -> retriever -> response).
"""

from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class State(TypedDict):
    """Shared state object passed between all LangGraph nodes."""

    programme: str                     # e.g. "BCA", "BBA", "B.Com (H)"
    messages: Annotated[list, add_messages]
    query_type: str                    # "academic" | "fee" | "general"
    retrieved_context: str             # chunks pulled from the relevant PDF
