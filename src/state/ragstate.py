from langchain_core.documents import Document
from pydantic import BaseModel, Field


class RAGstate(BaseModel):

    question: str

    chat_history: list[dict] = Field(default_factory=list)

    # "professional" for lawyers/law students, "normal" for laypeople.
    mode: str = "normal"

    # What the user picked in the language dropdown ("Auto ..." = match their message).
    language: str = "Auto (reply in my language)"

    # The language the answer was actually written in.
    reply_language: str = ""

    retrieved_docs: list[Document] = Field(default_factory=list)

    answer: str = ""

    context_quality: str = ""

    source_type: str = ""

    confidence: str = ""

    external_context: str = ""

    # "You need a real lawyer" warnings from the fixed rules in src/guards.
    escalations: list[dict] = Field(default_factory=list)

    # Every section / Act / case cited in the answer and whether it was found
    # in the sources (verified, wrong_act or unverified).
    citations: list[dict] = Field(default_factory=list)