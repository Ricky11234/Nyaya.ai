"""Graph builder for LangGraph workflow"""

from langgraph.graph import StateGraph, END

from src.state.ragstate import RAGstate
from src.nodes.node import Nodes


class GraphBuilder:

    def __init__(self, retriever, llm):

        self.nodes = Nodes(
            retriever,
            llm
        )

        self.graph = None

    def build(self):

        builder = StateGraph(RAGstate)

        builder.add_node(
            "agent",
            self.nodes.generate_ans
        )

        builder.set_entry_point(
            "agent"
        )

        builder.add_edge(
            "agent",
            END
        )

        self.graph = builder.compile()

        return self.graph

    def run(
        self,
        question: str,
        chat_history=None,
        mode: str = "normal",
        language: str = "Auto (reply in my language)"
    ):

        if self.graph is None:

            self.build()

        if chat_history is None:

            chat_history = []

        initial_state = RAGstate(
            question=question,
            chat_history=chat_history,
            mode=mode,
            language=language
        )

        return self.graph.invoke(
            initial_state
        )