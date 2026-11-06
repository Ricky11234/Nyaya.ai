"""Main application for Agentic RAG"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.config.config import Config
from src.document_ingestion.docu import docuprocessor
from src.vectorstore.faiss import Retriever
from src.graph_builder.g_builder import GraphBuilder
from src.language import languages
from src.assist import case_tools

PDF_DIR = Path("data/legal_pdfs")


def legal_pdfs():
    """Every PDF in data/legal_pdfs. To add a law, drop its PDF there: the
    search index is rebuilt automatically on the next start."""
    return sorted(str(p) for p in PDF_DIR.glob("*.pdf"))


class AgenticRAG:

    def __init__(self, srcs: list[str] = None):

        print("Initializing Agentic RAG...")

        self.srcs = srcs or legal_pdfs()
        srcs = self.srcs

        self.processor = docuprocessor(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )

        self.retriever = Retriever()

        # The index remembers which PDFs it was built from; if the PDFs in
        # data/legal_pdfs change, it is rebuilt instead of silently ignoring them.
        manifest = Path(self.retriever.INDEX_PATH) / "sources.json"
        wanted = sorted(Path(s).name for s in srcs)
        built_from = json.loads(manifest.read_text()) if manifest.exists() else None

        if self.retriever.index_exists() and built_from == wanted:

            print("Loading existing FAISS index...")

            self.retriever.load_retriever()

        else:

            print(f"Building search index from {len(srcs)} law PDFs (takes a few minutes)...")

            docs = self.processor.process(srcs)

            print(f"Created {len(docs)} chunks")

            self.retriever.create_retriever(docs)

            manifest.write_text(json.dumps(wanted, indent=2))

        self.llm = Config.get_llm()

        self.graph_builder = GraphBuilder(
            retriever=self.retriever,
            llm=self.llm
        )

        self.graph_builder.build()

        print("System Ready")

    def ask(self, question: str, chat_history=None, mode: str = "normal",
            language: str = languages.AUTO):

        if chat_history is None:
            chat_history = []

        result = self.graph_builder.run(
            question=question,
            chat_history=chat_history,
            mode=mode,
            language=language
        )

        answer = result["answer"]

        source_type = result.get(
         "source_type",
    ""
)

        confidence = result.get(
    "confidence",
    ""
)

        reply_language = result.get("reply_language", "")

        escalations = result.get("escalations", [])

        citations = result.get("citations", [])

        print("\nQuestion:")
        print(question)

        print("\nAnswer:")
        print(answer)

        return {
    "answer": answer,
    "source_type": source_type,
    "confidence": confidence,
    "reply_language": reply_language,
    "escalations": escalations,
    "citations": citations
}

    # ---------------------------------------------------------------- #
    # Helping people act: case file and drafts
    # ---------------------------------------------------------------- #

    def build_case(self, user_messages: list[str], language: str = "English") -> dict:
        """Turns what the person said (any language) into a structured case file."""
        # The smaller model: it does this well, and it has its own daily token
        # budget on Groq, so a full test run fits in one day.
        return case_tools.build_case(Config.get_evaluator_llm(), user_messages, language)

    def draft(self, case: dict, doc_type: str, language: str = "English") -> dict:
        """Drafts a legal notice / complaint / reply from the case file, citing
        only law found by searching the PDFs for this case."""
        query = f"{case.get('problem_type', '')}. {case.get('summary', '')}"
        law_docs = self.retriever.retrieve(query, k=6)
        return case_tools.draft(self.llm, case, doc_type, law_docs, language)

    def interactive_mode(self):

        print("\nInteractive Mode Started")

        choice = input(
            "Choose mode - [1] Professional  [2] Normal (default 2): "
        ).strip()

        mode = "professional" if choice == "1" else "normal"

        print("\nLanguages: " + ", ".join(languages.UI_CHOICES[1:]))
        lang = input(
            "Reply language (press Enter to reply in whatever language you type): "
        ).strip() or languages.AUTO

        print(f"Mode: {mode.title()} | Language: {lang}")
        print("Type 'quit' to exit\n")

        history = []

        while True:

            question = input("Enter Question: ").strip()

            if question.lower() in ["quit", "exit", "q"]:
                print("Goodbye")
                break

            if question:

                answer = self.ask(
                    question,
                    history,
                    mode,
                    lang
                )

                history.append(
                    {
                        "role": "user",
                        "content": question
                    }
                )

                history.append(
    {
        "role": "assistant",
        "content": answer["answer"]
    }
)

                print("-" * 80)


def main():

    rag = AgenticRAG(legal_pdfs())

    rag.interactive_mode()


if __name__ == "__main__":
    main()