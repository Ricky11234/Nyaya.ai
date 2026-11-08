from langchain_core.documents import Document
from pydantic import BaseModel, Field


class RAGstate(BaseModel):

    question: str

    chat_history: list[dict] = Field(default_factory=list)

    mode: str = "normal"

    language: str = "Auto (reply in my language)"

    reply_language: str = ""

    retrieved_docs: list[Document] = Field(default_factory=list)

    answer: str = ""

    context_quality: str = ""

    source_type: str = ""

    confidence: str = ""

    external_context: str = ""

    escalations: list[dict] = Field(default_factory=list)

    citations: list[dict] = Field(default_factory=list)

    faithfulness: dict | None = None
