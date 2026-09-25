r"""
agent.py
--------
Wires the nodes from tools/nodes.py into a LangGraph StateGraph and
compiles it into a runnable agent.

    classifier --> academic_rag --\
               \-> fee_rag --------> response --> END
               \-> general --------/
"""

from langgraph.graph import StateGraph, START, END

from state.StatePipeline import State
from tools.nodes import (
    classifier_node,
    academic_rag_node,
    fee_rag_node,
    general_node,
    response_node,
    route_query,
)


def build_agent():
    graph = StateGraph(State)

    graph.add_node("classifier", classifier_node)
    graph.add_node("academic_rag", academic_rag_node)
    graph.add_node("fee_rag", fee_rag_node)
    graph.add_node("general", general_node)
    graph.add_node("response", response_node)

    graph.add_edge(START, "classifier")

    graph.add_conditional_edges(
        "classifier",
        route_query,
        {
            "academic_rag": "academic_rag",
            "fee_rag": "fee_rag",
            "general": "general",
        },
    )

    graph.add_edge("academic_rag", "response")
    graph.add_edge("fee_rag", "response")
    graph.add_edge("general", "response")

    graph.add_edge("response", END)

    return graph.compile()


# Compiled, ready-to-invoke agent used by main.py
app = build_agent()
