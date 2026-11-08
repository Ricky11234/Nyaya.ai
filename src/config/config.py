import os
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


class Config:

    GROQ_API_KEY=os.getenv("GROQ_API_KEY") or st.secrets["GROQ_API_KEY"]

    TAVILY_API_KEY=os.getenv("TAVILY_API_KEY") or st.secrets["TAVILY_API_KEY"]

    LLM_MODEL=os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

    EVALUATOR_MODEL=os.getenv("EVALUATOR_MODEL", "openai/gpt-oss-20b")

    FALLBACK_MODEL=os.getenv("FALLBACK_MODEL", "qwen/qwen3.8-27b")

    FACT_CHECK_MODEL=os.getenv("FACT_CHECK_MODEL", "qwen/qwen3.8-27b")

    EMBEDDING_MODEL="all-MiniLM-L6-v2"

    CHUNK_SIZE=1200

    CHUNK_OVERLAP=200

    @classmethod
    def validate(cls):

        if not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY missing")

        if not cls.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY missing")

    @classmethod
    def _chat(cls, model, retries=2):
        extra = {}
        if model.startswith("qwen/"):
            extra["reasoning_format"] = "hidden"
        return ChatGroq(
            model=model,
            api_key=cls.GROQ_API_KEY,
            temperature=0,
            max_retries=retries,
            **extra
        )

    @classmethod
    def get_llm(cls):

        cls.validate()

        os.environ["TAVILY_API_KEY"]=cls.TAVILY_API_KEY

        fallback = cls.FALLBACK_MODEL
        if not fallback or fallback.lower() == "none" or fallback == cls.LLM_MODEL:
            return cls._chat(cls.LLM_MODEL)
        return cls._chat(cls.LLM_MODEL, retries=1).with_fallbacks([cls._chat(fallback)])

    @classmethod
    def get_evaluator_llm(cls):

        cls.validate()

        return cls._chat(cls.EVALUATOR_MODEL, retries=5)

    @classmethod
    def get_fact_check_llm(cls):

        cls.validate()

        return cls._chat(cls.FACT_CHECK_MODEL, retries=5)
