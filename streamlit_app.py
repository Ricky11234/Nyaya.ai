import json
import streamlit as st
import time

from main import AgenticRAG, legal_pdfs
from src.language import languages
from src.guards import guards
from src.assist.case_tools import DOC_TYPES, case_to_markdown, to_docx_bytes
from src.ui.theme import apply_theme, hero, loader

st.set_page_config(
    page_title="Nyaya.ai - Your AI Legal Friend",
    page_icon="⚖️",
    layout="wide"
)

apply_theme()

if "language" not in st.session_state:

    st.session_state.language = languages.AUTO

# Every PDF in data/legal_pdfs (add a law by dropping its PDF there).
LEGAL_DOCS = legal_pdfs()

COVERED = """- Consumer Protection Act, 2019 (refunds, defective goods)
- Information Technology Act, 2000 (online fraud, hacking)
- Bharatiya Nagarik Suraksha Sanhita, 2023 (arrest, FIR, bail)
- Code on Wages, 2019 (unpaid salary)
- Model Tenancy Act, 2021 (rent, deposit; only in states that adopted it)
- Protection of Women from Domestic Violence Act, 2005"""

# ---------------------------------------------------------------------- #
# Mode selection screen (shown until the user picks a mode)
# ---------------------------------------------------------------------- #

if "mode" not in st.session_state:

    hero("Your legal friend, in your language. Tell me what happened and I'll tell you where you stand.")

    st.subheader("How would you like your answers?")

    st.markdown(
        """
This assistant helps with everyday legal problems in India: refunds and
defective goods, online fraud, arrest and bail, unpaid salary, rent deposits
and domestic violence. It answers from the text of the laws, falls back to
official websites when they don't cover your question, tells you when you
need a real lawyer, and can draft a notice or complaint for you.

You can ask **in English, Hinglish or Hindi**, and also in Bengali, Tamil
or Odia (beta: these work, but are less tested).
"""
    )

    st.session_state.language = st.selectbox(
        "🗣️ Language for answers",
        languages.UI_CHOICES,
        index=languages.UI_CHOICES.index(st.session_state.language),
        help="On Auto, I reply in the same language you type in."
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### 👔 Professional Mode")

        st.markdown(
            """
For **lawyers and law students**.

- Detailed, fully bulleted answers
- Specific Act, provision and page cited for each point
- Precise legal terminology
"""
        )

        if st.button("Enter Professional Mode", use_container_width=True):

            st.session_state.mode = "professional"

            st.rerun()

    with col2:

        st.markdown("### 🧑 Normal Mode")

        st.markdown(
            """
For **anyone needing quick legal guidance**.

- Short, plain-language bullet-point overviews
- No legal jargon
- Sources named simply so you know where the info comes from
"""
        )

        if st.button("Enter Normal Mode", use_container_width=True):

            st.session_state.mode = "normal"

            st.rerun()

    st.stop()

# ---------------------------------------------------------------------- #
# Sidebar
# ---------------------------------------------------------------------- #

with st.sidebar:

    st.title("⚖️ Nyaya.ai")

    st.markdown(f"**Mode:** {st.session_state.mode.title()}")

    if st.button("🔄 Switch Mode"):

        del st.session_state["mode"]

        st.rerun()

    st.session_state.language = st.selectbox(
        "🗣️ Answer language",
        languages.UI_CHOICES,
        index=languages.UI_CHOICES.index(st.session_state.language),
        help="On Auto, I reply in the same language you type in. "
             "(beta) languages work but are less tested."
    )

    st.markdown("---")

    st.markdown(
        """
### About

Agentic Legal RAG System for Indian Laws.

Current Legal Corpus:

""" + COVERED + """

Features:

- FAISS Vector Search
- Corrective Agentic RAG
- Context Evaluation Agent
- Tavily Search Fallback
- Conversational Query Rewriting
- Source Attribution
- Confidence Scoring
- Hinglish, Hindi and regional language support
- "You need a lawyer" warnings (fixed rules)
- Citation check on every answer
- Case file and document drafting
"""
    )

    st.markdown("---")

    if st.button("🗑️ Clear Chat History"):

        st.session_state.chat_history = []

        st.session_state.case = None

        st.session_state.draft = None

        st.rerun()

hero("Your legal friend, in your language.")

st.markdown(
    """
Tell me your problem in your own words. I can:

- explain where you stand and what you can do, from the text of the law
- tell you when you need a real lawyer
- turn your story into a **case file** and **draft** a legal notice or complaint (below the chat)

I first search the law texts, then official websites if needed, and I check every section I cite.
"""
)

with st.expander("💡 Example Questions"):

    st.markdown(
        """
- What is cyber terrorism under the IT Act?
- What are consumer rights under the Consumer Protection Act?
- What is a cognizable offence under BNSS?
- What penalties exist for data theft?
- What amendments were introduced to the IT Act in 2025?
- Online order ka refund 2 mahine se nahi aaya, kya karun?
- मेरे अकाउंट से UPI फ्रॉड में पैसे कट गए, क्या करूँ?
- My landlord won't return my security deposit after I moved out.
- Meri company ne 3 mahine se salary nahi di. Kya karun?
"""
    )

@st.cache_resource
def load_rag():

    return AgenticRAG(LEGAL_DOCS)

try:

    rag_system = load_rag()

except Exception as e:

    st.error(f"System Initialization Failed: {e}")

    st.stop()

if "chat_history" not in st.session_state:

    st.session_state.chat_history = []

st.session_state.setdefault("case", None)

st.session_state.setdefault("draft", None)


def render_answer(meta, answer):
    """Banners, answer and citation check for one assistant message."""

    for f in meta.get("escalations", []):
        st.error("🧑‍⚖️ " + f["message"])

    source_type = meta.get("source_type")
    confidence = meta.get("confidence", "LOW")
    label = {"vectorstore": "📚 Source: Legal Corpus", "external": "🌐 Source: External Search"}.get(
        source_type, "⚠️ System Response"
    )
    banner = f"{label} | {confidence.title()} Confidence"
    if confidence == "HIGH":
        st.success(banner)
    elif confidence == "MEDIUM":
        st.warning(banner)
    else:
        st.error(banner)

    st.markdown(answer)

    citations = meta.get("citations", [])
    if citations:
        with st.expander("🔎 Citation check"):
            for c in citations:
                mark = "✅" if c["status"] == "verified" else "❌"
                st.markdown(f"{mark} {guards.describe(c)}: {c['status'].replace('_', ' ')}")

    if meta.get("caption"):
        st.caption(meta["caption"])


def current_language():
    for m in reversed(st.session_state.chat_history):
        if m["role"] == "assistant" and m.get("meta", {}).get("reply_language"):
            return m["meta"]["reply_language"]
    return languages.resolve(st.session_state.language, "English")


for msg in st.session_state.chat_history:

    with st.chat_message(msg["role"]):

        if msg["role"] == "assistant":
            render_answer(msg.get("meta", {}), msg["content"])
        else:
            st.markdown(msg["content"])

# ---------------------------------------------------------------------- #
# Case file and drafting (help the person act, not just understand)
# ---------------------------------------------------------------------- #

user_msgs = [m["content"] for m in st.session_state.chat_history if m["role"] == "user"]

if user_msgs:

    with st.expander("📁 My case file: what happened, when, and what proof you have"):

        if st.button("Build / update my case file", type="primary"):
            box = loader("Organising your story into a case file...", "Only what you told me goes in. Nothing is made up.")
            st.session_state.case = rag_system.build_case(user_msgs, current_language())
            box.empty()

        if st.session_state.case:
            st.markdown(case_to_markdown(st.session_state.case))
            st.download_button(
                "Download case file (JSON)",
                json.dumps(st.session_state.case, indent=2, ensure_ascii=False),
                "case_file.json",
                "application/json",
            )

    with st.expander("📝 Draft a legal notice, complaint or reply"):

        doc_type = st.selectbox("What do you need?", list(DOC_TYPES))

        if st.button("Draft it", type="primary"):
            box = loader(f"Drafting your {doc_type.lower()}...", "Finding the right law first, then writing it up.")
            if not st.session_state.case:
                st.session_state.case = rag_system.build_case(user_msgs, current_language())
            st.session_state.draft = {
                "type": doc_type,
                **rag_system.draft(st.session_state.case, doc_type, current_language()),
            }
            box.empty()

        if st.session_state.draft:
            st.caption("Fill in everything in [SQUARE BRACKETS] before sending. You can edit the text here.")
            edited = st.text_area("Draft", st.session_state.draft["text"], height=450)
            c1, c2 = st.columns(2)
            c1.download_button("Download .txt", edited, f"{st.session_state.draft['type']}.txt")
            c2.download_button(
                "Download .docx",
                to_docx_bytes(edited, st.session_state.draft["type"]),
                f"{st.session_state.draft['type']}.docx",
            )

question = st.chat_input(
    "Ask in English, Hinglish, Hindi or your own language..."
)

if question:

    history_for_model = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.chat_history
    ]

    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": question
        }
    )

    with st.chat_message("user"):

        st.markdown(question)

    box = loader("Weighing your case...")

    start = time.time()

    try:

        result = rag_system.ask(
            question,
            history_for_model,
            st.session_state.mode,
            st.session_state.language
        )

    except Exception as e:

        result = {
            "answer": f"Error: {e}",
            "source_type": "system",
            "confidence": "LOW",
        }

    elapsed = time.time() - start

    box.empty()

    reply_language = result.get("reply_language", "")

    meta = {
        "source_type": result.get("source_type"),
        "confidence": result.get("confidence", "LOW"),
        "reply_language": reply_language,
        "escalations": result.get("escalations", []),
        "citations": result.get("citations", []),
        "caption": f"⏱️ Response Time: {elapsed:.2f} seconds"
        + (f" | 🗣️ Answered in: {reply_language}" if reply_language else ""),
    }

    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "meta": meta
        }
    )

    st.rerun()
