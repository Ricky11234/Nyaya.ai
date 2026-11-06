from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


class Retriever:

    INDEX_PATH = "data/faiss_index"

    def __init__(self):

        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.vectorstore = None
        self.retriever = None

    def create_retriever(self, docs: list[Document]):

        if not docs:
            raise ValueError("No documents provided")

        print("Creating FAISS index...")

        self.vectorstore = FAISS.from_documents(
            docs,
            self.embeddings
        )

        self.vectorstore.save_local(
            self.INDEX_PATH
        )

        print(
            f"FAISS index saved to {self.INDEX_PATH}"
        )

        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 8}
        )

    def load_retriever(self):

        index_folder = Path(
            self.INDEX_PATH
        )

        if not index_folder.exists():

            raise FileNotFoundError(
                f"No FAISS index found at {self.INDEX_PATH}"
            )

        print(
            "Loading existing FAISS index..."
        )

        self.vectorstore = FAISS.load_local(
            self.INDEX_PATH,
            self.embeddings,
            allow_dangerous_deserialization=True
        )

        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 8}
        )

        print(
            "FAISS index loaded successfully."
        )

    def index_exists(self):

        index_folder = Path(
            self.INDEX_PATH
        )

        return (
            index_folder.exists()
            and (index_folder / "index.faiss").exists()
            and (index_folder / "index.pkl").exists()
        )

    def retrieve(
        self,
        query: str,
        k: int = 4
    ) -> list[Document]:

        if self.retriever is None:

            raise ValueError(
                "Retriever not initialized. "
                "Call create_retriever() or load_retriever() first."
            )

        response = self.retriever.invoke(
            query
        )

        return response[:k]

    def get_retriever(self):

        if self.retriever is None:

            raise ValueError(
                "Retriever not initialized."
            )

        return self.retriever