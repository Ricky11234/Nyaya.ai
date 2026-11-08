# ⚖️ Nyaya.ai

**Your AI legal friend, in your language.** Nyaya (न्याय) means *justice*.

It answers in English, Hinglish, Hindi and regional languages, warns when you need a real lawyer, checks every citation, scores how well each answer is grounded in the law (and revises it if not), and helps draft notices and complaints.

An Agentic Retrieval-Augmented Generation (RAG) system for answering questions related to Indian laws using legal document retrieval, large language models, and corrective web search.

The system first searches a curated legal corpus and evaluates whether the retrieved information is sufficient to answer the user's query. If the information is unavailable or incomplete, it automatically performs external search and transparently informs the user about the source of the answer.

---

## 🎯 Project Motivation

Legal information is often scattered across lengthy documents and legislative texts, making it difficult for citizens to quickly find relevant information.

This project aims to build an intelligent legal assistant capable of:

* Understanding natural language questions
* Retrieving relevant legal provisions
* Providing structured explanations
* Handling follow-up questions
* Transparently indicating information sources
* Falling back to external search when the legal corpus is insufficient

---

## 🚀 Features

### 📚 Legal Corpus Search

Current legal corpus includes:

* Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023: arrest, FIR, bail
* Information Technology Act, 2000: online fraud, hacking, identity theft
* Consumer Protection Act, 2019: refunds, defective goods, bad service
* Code on Wages, 2019: unpaid salary (in force from 21 Nov 2025)
* Model Tenancy Act, 2021: rent and deposits (a model law: applies only in states that adopted it, and the app says so)
* Protection of Women from Domestic Violence Act, 2005 (text from Indian Kanoon, not the Gazette copy)

To add a law, drop its PDF into `data/legal_pdfs/` and add a filename keyword to `SOURCE_NAMES` in `src/nodes/node.py`. The search index notices the new file and rebuilds itself on the next start (`data/faiss_index/sources.json` records which PDFs it was built from).

### 🔍 Semantic Retrieval

* Sentence Transformer Embeddings
* FAISS Vector Database
* Persistent Local Index
* Fast Similarity Search

### 🤖 Agentic RAG Pipeline

* Retrieval Agent
* Context Evaluation Agent
* Corrective RAG Workflow
* Source Attribution Layer

### 💬 Conversational Legal Assistant

* Follow-up Questions
* Context-Aware Query Rewriting
* Multi-Turn Conversations

### 🌐 Corrective Web Search

When information is not available in the legal corpus:

* Tavily Search Integration
* Automatic Information Retrieval
* Transparent Source Disclosure

### 📊 Confidence & Source Attribution

Every response is classified as:

| Source             | Confidence |
| ------------------ | ---------- |
| 📚 Legal Corpus    | High       |
| 🌐 External Search | Medium     |
| ⚠️ System Response | Low        |

### 🖥️ Interactive Interface

* Streamlit Chat UI
* Response Time Monitoring
* Chat History
* Example Questions
* One-Click Chat Reset

### 🗣️ Hinglish, Hindi and Regional Languages

Ask in the language you are comfortable with. On **Auto**, the assistant replies in the language you typed in; you can also pick a language from the dropdown.

| Language | Status |
| -------- | ------ |
| English, Hinglish (Hindi in Roman letters), Hindi | Supported |
| Bengali, Tamil, Odia | Beta: passed our tests, but less tested |

How it works: the law PDFs and the embedding model are English-only, so every question is first rewritten into a standalone **English** question (this also folds in earlier chat turns) and that English question is used for the FAISS search. Only the final answer is written in the user's language. Act names and section numbers stay in English so they can be checked. Scripts like Tamil, Bengali or Odia are detected from the characters themselves; the model decides between English and Hinglish.

---

### 🧑‍⚖️ Knowing When You Need a Real Lawyer

Fixed rules in code (`src/guards/guards.py`), not the model, decide when to warn the user. They cover arrest or custody, court papers or deadlines, violence, self-harm, large amounts (₹10 lakh+), and court cases, property or divorce. The warning appears as a red banner, and the answer repeats it in the user's language with the NALSA free legal aid number (15100). "Digital arrest" calls are recognised as a scam, not an arrest.

### 🔎 Citation Check (how it avoids invented laws)

Every section number, Act name and case name in an answer is checked in code against the text the answer was given: the retrieved law pages, or the web results. Anything not found there, or a real section credited to the wrong Act, is listed under the answer as **"Not verified"** and the confidence drops one level. Fixed, checked facts (helplines, e-Jagriti, consumer commission limits, which laws are in force) are given to the model so it doesn't have to remember them. Web fallback is limited to government and well-known legal sites.

### ✅ Fact Check (groundedness score)

The citation check only covers section numbers, Act names and case names. A second check covers everything else: a separate model (Qwen 3.8 27B, set by `FACT_CHECK_MODEL`) lists each factual claim in the answer (rights, deadlines, amounts, penalties, which authority to approach, helplines) and marks each one as supported or not by the exact sources the answer was given. The app shows the score ("6/7 claims found in the sources") and lists any unsupported claim under the answer. Below 80% the confidence drops one level; below 50% it drops to Low. If the checker fails or hits a rate limit, the answer is still shown, marked "not checked".

### 🔁 Automatic Revision

If the citation check or the fact check flags anything, the main model rewrites the answer once, given the list of problems and the same sources: it corrects each point from the sources, or removes it, or says it isn't sure. Both checks then run again, and the app keeps whichever version has fewer problems. Anything still unresolved stays flagged under the answer.

### 🔍 Searching in the Law's Own Words

People say "anticipatory bail" or "police picked up my brother"; the Acts say "bail to person apprehending arrest" and "person arrested to be informed of grounds of arrest". For common problems, the app adds the Act's own wording to the search (`STATUTE_WORDING` in `src/guards/guards.py`), so the right sections are found.

What the checks can't catch: the checker is itself a model, so it can miss a wrong claim or flag a correct one. That's why every flag is shown to the user rather than hidden, and why the app tells people to confirm with a lawyer.

### 📁 Case File and 📝 Drafting

Below the chat, the app can turn everything the user said into a **case file**: what happened and when, the other party, the amount, proof they have, proof to collect, and questions for missing facts. From that it **drafts** a legal notice, consumer complaint, cyber crime complaint, reply to a notice, or complaint email, as editable text with .txt/.docx download. Missing facts become `[PLACEHOLDERS]` instead of being invented, and sections cited in the draft are checked the same way.

---

# 🧪 Testing

```bash
python tests/run_cases.py        # 15 test cases incl. hallucination and "guarantee I'll win" traps
python test_languages.py         # 9 language cases (English, Hinglish, Hindi, Tamil, Odia, Bengali)
```

Unedited outputs go to `outputs/raw/` and `outputs/language_tests/`, with a summary table in `outputs/summary.md`. The automatic checks are signals, not a grade; each answer still needs a human read.

---

# 🏗️ System Architecture

```text
User question (any language) + chat history
        │
        ▼
Rewrite to English question + legal search terms      (GPT-OSS 120B)
        │
        ▼
Reply language  ·  Lawyer-warning rules               (code)
        │
        ▼
FAISS search over the Acts + Act's own wording        (code)
        │
        ▼
Is this law text enough?                              (GPT-OSS 20B)
        │
 ┌──────┴──────┐
 ▼             ▼
SUFFICIENT   INSUFFICIENT
Answer from  Web search (gov + legal sites)
the Acts     → answer from the web
 └──────┬──────┘
        ▼
Citation check (code) + groundedness score            (Qwen 3.8 27B)
        │
        ▼
Problems? → rewrite once → check again → keep the better version
        │
        ▼
Flags, old-law / model-law warnings, confidence       (code)
        │
        ▼
Answer + banners + fact check  →  optional case file and draft
```

---

# 🛠️ Tech Stack

## LLMs

* GPT-OSS 120B on Groq (`openai/gpt-oss-120b`): rewriting, translation, answers and drafts. Groq's strongest production model.
* GPT-OSS 20B on Groq (`openai/gpt-oss-20b`): context evaluator and case file. Fast, and on its own daily budget.
* Qwen 3.8 27B on Groq (`qwen/qwen3.8-27b`, preview): the fact check, and automatic backup when the main model hits its daily limit. Running the fact check on a separate model keeps it off the other models' rate limits.
* All of them can be changed in `.env` (`LLM_MODEL`, `EVALUATOR_MODEL`, `FALLBACK_MODEL`, `FACT_CHECK_MODEL`) without touching code. Groq retired the Llama 3.x models this project started on in Aug 2026, and the swap was a one-line change.

## Frameworks

* LangChain
* LangGraph
* Streamlit

## Vector Database

* FAISS

## Embeddings

* all-MiniLM-L6-v2

## External Search

* Tavily Search API

---

# 📂 Project Structure

```text
Nyaya.ai/
├── data/
│   ├── legal_pdfs/          # the 6 law PDFs the answers come from
│   └── faiss_index/         # prebuilt search index (+ sources.json: which PDFs it was built from)
├── src/
│   ├── config/              # API keys and model names
│   ├── document_ingestion/  # PDF loading and chunking
│   ├── vectorstore/         # FAISS index build/load
│   ├── language/            # supported languages + language detection
│   ├── nodes/               # the agent: rewrite, retrieve, evaluate, answer, check
│   ├── guards/              # lawyer-warning rules and citation check (plain code, no AI)
│   ├── assist/              # case file and drafting (notice, complaint, reply)
│   ├── graph_builder/       # LangGraph wiring
│   ├── state/               # the state passed through the graph
│   └── ui/                  # Streamlit theme and loader
├── tests/
│   ├── cases.json           # 15 test cases
│   └── run_cases.py         # runs them and saves raw outputs
├── outputs/                 # raw, unedited test outputs + summary.md
├── assets/hero.jpg          # header photo
├── .streamlit/config.toml   # app colours
├── streamlit_app.py         # the web app
├── main.py                  # AgenticRAG class + terminal mode
├── test_languages.py        # 9 language test cases
├── requirements.txt
└── .env.example
```

---

# ⚙️ Running Locally

You need **Python 3.11 or newer** (developed on 3.13), and two free API keys:

* Groq: https://console.groq.com/keys (the AI model)
* Tavily: https://app.tavily.com (web search fallback)

## 1. Clone the repository

```bash
git clone https://github.com/<your-username>/Nyaya.ai.git
cd Nyaya.ai
```

## 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

| Your terminal | Activate with |
| --- | --- |
| Windows Command Prompt (cmd) | `.venv\Scripts\activate.bat` |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| macOS / Linux | `source .venv/bin/activate` |

When it worked, your prompt starts with `(.venv)`. (Using uv instead? `uv venv` then the same activate command.)

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

The first install takes a few minutes (PyTorch comes with sentence-transformers).

## 4. Add your API keys

Copy `.env.example` to `.env` and paste in your keys:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

`.env` is in `.gitignore`, so your keys never get pushed.

Optional: to try a different model, add `LLM_MODEL=...` and/or `EVALUATOR_MODEL=...` (any chat model listed at https://console.groq.com/docs/models). Nothing else needs to change.

## 5. Run the app

```bash
python -m streamlit run streamlit_app.py
```

It opens at http://localhost:8501. The first start takes a minute: it downloads the small embedding model (about 90 MB, once) and loads the search index from `data/faiss_index/`.

Prefer the terminal? `python main.py` runs the same assistant as a text chat.

## 6. Run the tests (optional)

```bash
python tests/run_cases.py           # all 15 cases, about 10-15 minutes
python tests/run_cases.py 06 12     # only some cases
python test_languages.py            # the 9 language cases
```

To compare models, set one for this terminal window and save to its own folder (cmd shown; PowerShell uses `$env:LLM_MODEL="..."`):

```bash
set LLM_MODEL=qwen/qwen3.8-27b
python tests/run_cases.py --out outputs/models/qwen3.8-27b
```

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `ModuleNotFoundError` | The virtual environment isn't active. Activate it (step 2) and try again. |
| `Activate.ps1` does nothing in cmd | That script is for PowerShell. In cmd use `activate.bat`. |
| Error 429, or "hit its free daily usage limit" | Groq's free tier allows about 200,000 tokens a day per model. Wait a while (it frees up gradually over 24 hours), or set a different `LLM_MODEL` in `.env`. |
| Error 404 `model_not_found` | Groq retired that model. Pick a current one from the Groq models page and set `LLM_MODEL` in `.env`. |
| Added a PDF but answers ignore it | Add a filename keyword to `SOURCE_NAMES` in `src/nodes/node.py`; the index rebuilds on the next start. |

---

# ☁️ Deploying on Streamlit Cloud

1. Push the repository to GitHub (with `data/faiss_index/`, so the app doesn't rebuild it)
2. At https://share.streamlit.io, create a new app from the repo, main file `streamlit_app.py`
3. In **Advanced settings → Secrets**, add:

```toml
GROQ_API_KEY="your_groq_api_key"
TAVILY_API_KEY="your_tavily_api_key"
```

4. Deploy

---

# 🚧 Known Limitations

* **Free-tier limits:** on Groq's free tier each question uses roughly 6,000-8,000 tokens of the 200,000-token daily allowance, so the app handles about 25-30 questions a day before it pauses (a paid Groq tier removes this).
* **The fact check is a model too:** numbers and deadlines are now checked against the sources, but by a second model that can occasionally miss a wrong claim or flag a correct one. It also adds a few thousand tokens per question.
* **Regional languages are beta:** Bengali, Tamil and Odia passed our tests but have been tested less than English, Hinglish and Hindi. Other languages get an English reply.
* **State laws aren't covered:** rent, stamp duty and many labour rules differ by state. The app says so, but it only has the central Acts listed above.
* **Not a lawyer:** it gives legal information and drafts, not legal advice.

---

# ⚠️ Disclaimer

This project is intended for educational and research purposes only.

The responses generated by the system should not be considered legal advice. Always consult qualified legal professionals before making legal decisions.
