import json
import re
from pathlib import Path

from src.state.ragstate import RAGstate
from src.config.config import Config
from src.language import languages
from src.guards import guards

from langchain_core.documents import Document
from langchain_community.tools.tavily_search import TavilySearchResults


class Nodes:

    # Maps keywords found in the PDF filenames to clean, citable names.
    # Adjust the keys to match your actual filenames in data/.
    SOURCE_NAMES = {
        "bnss": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "nagarik": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "it_act": "Information Technology Act, 2000",
        "information_technology": "Information Technology Act, 2000",
        "consumer": "Consumer Protection Act, 2019",
        "cp act": "Consumer Protection Act, 2019",
        # Added to cover the Kuku brief's everyday problems:
        "wages": "Code on Wages, 2019",
        "tenancy": "Model Tenancy Act, 2021",
        "domestic": "Protection of Women from Domestic Violence Act, 2005",
    }

    # Checked, current facts the model may use instead of guessing portals or
    # phone numbers (testing showed it still suggesting the retired e-Daakhil).
    OFFICIAL_FACTS = """- Consumer complaints are filed online on e-Jagriti (e-jagriti.gov.in), which replaced e-Daakhil. National Consumer Helpline: 1915.
- Which consumer commission (by value of goods/services paid): District Commission up to Rs 50 lakh; State Commission Rs 50 lakh to Rs 2 crore; National Commission above Rs 2 crore.
- Cyber fraud: call 1930 immediately and report at cybercrime.gov.in.
- Free lawyer / legal aid: NALSA helpline 15100.
- Emergency: 112. Women's helpline: 181.
- The Model Tenancy Act, 2021 is a model law: it applies only in states that have passed a law based on it. Elsewhere, deposit and rent disputes depend on the state's own rent law and the rent agreement; say this whenever you rely on it.
- The Code on Wages, 2019 is in force from 21 November 2025 and replaced the Payment of Wages Act, 1936 and the Minimum Wages Act, 1948.
- Unpaid salary: complaint to the Labour Commissioner/Inspector of the state, or the SAMADHAN portal (samadhan.labour.gov.in) for the central sphere."""

    WEB_DOMAINS = [
        "indiacode.nic.in", "gov.in", "nic.in", "e-jagriti.gov.in",
        "consumerhelpline.gov.in", "cybercrime.gov.in", "nalsa.gov.in",
        "rbi.org.in", "labour.gov.in", "sci.gov.in", "indiankanoon.org",
        "prsindia.org", "livelaw.in", "barandbench.com",
    ]

    def __init__(self, retriever, llm):

        self.retriever = retriever

        self.llm = llm

        self.evaluator_llm = Config.get_evaluator_llm()

        # Web fallback only from government and well-known legal sites. In
        # testing, unrestricted search returned random law blogs.
        self.tavily = TavilySearchResults(
            max_results=5,
            include_domains=self.WEB_DOMAINS
        )

    # ----------------------------------------------------------------- #
    # Helpers
    # ----------------------------------------------------------------- #

    def _friendly_source(self, raw: str) -> str:
        """Turn a raw file path into a clean, citable law name."""

        stem = Path(str(raw)).stem
        low = stem.lower()

        for key, name in self.SOURCE_NAMES.items():
            if key in low:
                return name

        return stem.replace("_", " ").replace("-", " ").title()

    def _format_external(self, raw_results):
        """
        Turn Tavily output into (context_text, sources_list).

        Tavily returns a list of dicts with 'url'/'content' (and sometimes
        'title'). On failure external_search returns an error string, which
        we pass through unchanged with no sources.
        """

        if isinstance(raw_results, str):
            return raw_results, []

        if isinstance(raw_results, list):

            parts = []
            sources = []

            for r in raw_results:

                if isinstance(r, dict):

                    url = r.get("url", "")
                    title = r.get("title") or url or "Web result"
                    content = r.get("content", "")

                    if url:
                        sources.append(f"{title} — {url}")

                    parts.append(f"{content}\n(Source: {url})")

                else:
                    parts.append(str(r))

            return "\n\n".join(parts), sources

        return str(raw_results), []

    @staticmethod
    def _lawyer_block(flags):
        """Prompt text that makes the answer itself repeat the lawyer warning,
        in the user's language (the app also shows it as a red banner)."""
        if not flags:
            return ""
        msgs = "\n".join(f"- {f['message']}" for f in flags)
        return f"""
IMPORTANT: Near the top of the answer, clearly tell the person this
(in the reply language), and do not promise any outcome:
{msgs}
"""

    def _check_answer(self, answer, docs, web_text, base_confidence):
        """Checks every citation in the answer against the text it came from.
        Unverified ones are listed under the answer and the confidence drops
        one level (HIGH -> MEDIUM -> LOW)."""
        law_pages = [
            (self._friendly_source(d.metadata.get("source", "")), d.page_content)
            for d in docs
        ]
        citations = guards.verify_citations(answer, law_pages, web_text)
        note = guards.warning_note(citations)
        caveat = guards.tenancy_caveat(answer)
        confidence = base_confidence
        answer += note + caveat
        # An old law mentioned as history is not an error, so it alone doesn't lower confidence.
        if caveat or any(c["status"] not in ("verified", "repealed") for c in citations):
            confidence = {"HIGH": "MEDIUM", "MEDIUM": "LOW"}.get(base_confidence, "LOW")
        bad = sum(c["status"] not in ("verified", "repealed") for c in citations)
        print(f"Citations checked: {len(citations)}, not verified: {bad}, confidence: {confidence}")
        return answer, citations, confidence

    # ----------------------------------------------------------------- #
    # LLM steps
    # ----------------------------------------------------------------- #

    def rewrite_question(
        self,
        question: str,
        chat_history: list
    ) -> tuple[str, str, str]:
        """Rewrites the latest message as a standalone ENGLISH question and
        detects the language it was written in.

        It now runs even without chat history, because the law PDFs and the
        embedding model are English-only: a Hinglish, Hindi or Tamil question
        has to be translated before the FAISS search can find anything.

        It also asks for a search query in legal wording: plain-English
        questions ("police took my brother") matched the formal text of the
        Acts poorly in testing, so the right sections were often not found.

        Returns (english_question, detected_language, search_query).
        """

        recent_history = chat_history[-6:] if chat_history else []

        history_text = "\n".join(
            [
                f"{msg['role']}: {msg['content']}"
                for msg in recent_history
            ]
        ) or "(no earlier messages)"

        prompt = f"""
You are a query rewriting assistant for an Indian legal-help app.

Conversation History:

{history_text}

Latest User Question:

{question}

Return ONLY a JSON object:
{{"english_question": "...", "language": "...", "search_query": "..."}}

- english_question: the latest question rewritten as ONE standalone question in clear English.
  Translate it if it is not in English. Include any details from the conversation history
  that are needed (amounts, dates, who did what). Do not add facts that were not said.
- language: the language of the latest question. One of: English, Hinglish, Hindi,
  Bengali, Tamil, Odia, Other. Use "Hinglish" for Hindi typed in
  Roman (English) letters, even when mixed with English words.
- search_query: a short search query in the formal legal wording an Indian Act
  would use for this situation, to find the right sections in the law text.
  Example: for "police took my brother and didn't say why" ->
  "arrest without warrant, grounds of arrest to be informed, arrested person
  to inform relative, production before Magistrate within twenty-four hours".
  Use only terms; do not state section numbers.
"""

        response = self.llm.invoke(prompt)

        text = response.content.strip()

        rewritten_question = question
        model_guess = "English"
        search_query = ""

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                rewritten_question = (data.get("english_question") or "").strip() or question
                model_guess = data.get("language", "English")
                search_query = (data.get("search_query") or "").strip()
            except json.JSONDecodeError:
                pass

        detected_language = languages.detect_language(question, model_guess)

        print(f"\nOriginal Question: {question}")
        print(f"Rewritten Question: {rewritten_question}")
        print(f"Detected Language: {detected_language}")
        print(f"Search Query: {search_query or '(same as question)'}")

        return rewritten_question, detected_language, search_query

    def evaluate_context(self, question: str, context: str) -> str:

        # The old wording ("answered accurately and COMPLETELY using ONLY the
        # context") made the gpt-oss evaluator reject the law text every time,
        # so even questions the PDFs clearly cover went to web search.
        prompt = f"""
You are a retrieval evaluator for an Indian legal-help assistant.

Question:
{question}

Retrieved text from Indian law documents:
{context}

Answer SUFFICIENT if this text contains the legal provisions that apply to the
person's situation (for example their right to complain, where to complain,
time limits, punishment, procedure, or their rights), even if it does not
cover every practical detail.

Answer INSUFFICIENT only if the text is about a different topic or a different
law, or is missing the provisions needed to explain where the person stands.

Return ONLY one word:

SUFFICIENT

or

INSUFFICIENT
"""

        # gpt-oss sometimes spends its output on reasoning and returns an empty
        # string; one retry fixed this in testing.
        result = ""
        for _ in range(2):
            result = (self.evaluator_llm.invoke(prompt).content or "").strip().upper()
            if result:
                break

        print(f"Evaluator Output: {result}")

        if result.startswith("INSUFFICIENT"):
            return "INSUFFICIENT"

        if result.startswith("SUFFICIENT"):
            return "SUFFICIENT"

        return "INSUFFICIENT"

    def external_search(self, question: str):

        try:

            # Without "India" a bare question like "my refund hasn't come"
            # returned US tax (IRS) pages in testing.
            result = self.tavily.invoke(f"{question} (India, Indian law)")

            print("Tavily Search Triggered")

            return result

        except Exception as e:

            return f"External search failed: {str(e)}"

    def generate_corrective_answer(
        self,
        question: str,
        external_context: str,
        sources: list,
        mode: str = "normal",
        language: str = "English",
        lawyer_block: str = ""
    ) -> str:

        source_block = (
            "\n".join(f"- {s}" for s in sources)
            if sources
            else "- External web search"
        )

        if mode == "professional":

            style = f"""
Provide a DETAILED answer aimed at a legal professional.
- Use clear bullet points, one distinct point per bullet.
- Where possible, attribute each point to the specific web source it came from.
- If information comes from a proposed bill, draft amendment, consultation paper,
  or news report, explicitly flag this on the relevant point.
- Use precise legal terminology.
- After the answer, add a "Sources:" section listing:
{source_block}
"""

        else:

            style = """
Provide a SHORT, plain-language overview for a non-lawyer.
- Use 3 to 6 simple bullet points, with no legal jargon.
- If anything is only a proposal, draft, or news (not settled law), say so plainly.
- End with one simple line naming where this came from, e.g. "Based on: web search".
"""

        prompt = f"""
You are an AI legal assistant specialized in Indian laws.

LANGUAGE RULE (most important): {languages.instruction(language)}
This applies to EVERY sentence you write, including the sentence saying the
answer was not found in the legal corpus. Only the two fixed lines
"Source: External Search" and "Confidence Level: Medium" stay in English.

QUESTION:
{question}

EXTERNAL INFORMATION:
{external_context}

Instructions:

1. Begin with:

Source: External Search

2. Explain that the answer was not found in the uploaded legal corpus.

3. Use the external information to answer.

4. Background for you only (do not repeat or explain it in the answer):
   since 1 July 2024 the IPC, CrPC and Indian Evidence Act are replaced by the
   BNS, BNSS and BSA. So never present an IPC or CrPC section as the law in force.

5. Mention a section number, monetary limit or deadline ONLY if it is written
   in the EXTERNAL INFORMATION above. If it is not there, describe the rule
   without a number. Never invent case names.

{lawyer_block}
6. OFFICIAL FACTS (current and correct). Mention one ONLY if it fits this
   person's problem (e.g. e-Jagriti and 1915 only for consumer problems, 1930
   only for cyber fraud). Do not list them all:
{self.OFFICIAL_FACTS}

{style}

End with:

Confidence Level: Medium

Remember: {languages.instruction(language)}
"""

        response = self.llm.invoke(prompt)

        return response.content

    def generate_rag_answer(
        self,
        question: str,
        context: str,
        mode: str = "normal",
        language: str = "English",
        lawyer_block: str = ""
    ) -> str:

        if mode == "professional":

            style = """
Provide a DETAILED answer aimed at a legal professional.
- Use clear bullet points, one distinct point per bullet.
- After each point, cite the exact source shown in the context in brackets,
  e.g. [Bharatiya Nagarik Suraksha Sanhita, 2023, p. 4].
- Reference specific sections or provisions where they appear in the context.
- Use precise legal terminology.
- End with a "Sources:" section listing every law referenced.
"""

        else:

            style = """
Provide a SHORT, plain-language overview for a non-lawyer.
- Use 3 to 6 simple bullet points, with no legal jargon.
- Keep it easy to understand.
- End with one simple line: "Based on: <law name(s)>" naming the source law(s)
  from the context above.
"""

        prompt = f"""
You are an AI legal assistant specialized in Indian laws.

LANGUAGE RULE (most important): {languages.instruction(language)}
This applies to every sentence of the answer.

Use ONLY the legal context below for legal statements. Mention a section
number only if it appears in the context, and say only what that section's
text in the context actually says it does. You may add practical next steps
(what proof to keep, who to contact), but do not invent laws, limits or cases.

OFFICIAL FACTS (current and correct). Mention one ONLY if it fits this
person's problem (e.g. e-Jagriti and 1915 only for consumer problems, 1930
only for cyber fraud). Do not list them all:
{self.OFFICIAL_FACTS}

LEGAL CONTEXT:
{context}
{lawyer_block}
QUESTION:
{question}

{style}

Remember: {languages.instruction(language)}

ANSWER:
"""

        response = self.llm.invoke(prompt)

        return response.content

    # ----------------------------------------------------------------- #
    # Main node
    # ----------------------------------------------------------------- #

    def generate_ans(self, state: RAGstate) -> RAGstate:

        reply_language = languages.resolve(state.language, "English")

        try:

            rewritten_question, detected_language, search_query = self.rewrite_question(
                state.question,
                state.chat_history
            )

            # The user's dropdown choice wins; on "Auto" we reply in the
            # language they wrote in.
            reply_language = languages.resolve(state.language, detected_language)

            # Fixed rules (not the model) decide when to send them to a lawyer.
            user_turns = [m["content"] for m in state.chat_history if m.get("role") == "user"]
            escalations = guards.escalation_flags(state.question, rewritten_question, *user_turns)
            lawyer_block = self._lawyer_block(escalations)
            print("Lawyer check:", [f["rule"] for f in escalations] or "none")

            # 6 chunks instead of the default 4: with 4, refund questions often
            # got only mediation/product-liability pages, not the complaint sections.
            # Search with the question plus its legal wording. The answer is
            # still written only from what this search finds.
            docs: list[Document] = self.retriever.retrieve(
                f"{rewritten_question} {search_query}".strip(),
                k=6
            )

            for d in docs:
                print(
                    "Retrieved:",
                    self._friendly_source(d.metadata.get("source", "")),
                    "p.", d.metadata.get("page"),
                    "|", d.page_content[:80].replace("\n", " ")
                )

            if not docs:

                print("No documents retrieved. Switching to Tavily.")

                raw = self.external_search(rewritten_question)

                external_context, ext_sources = self._format_external(raw)

                answer = self.generate_corrective_answer(
                    rewritten_question,
                    external_context,
                    ext_sources,
                    state.mode,
                    reply_language,
                    lawyer_block
                )

                answer, citations, confidence = self._check_answer(
                    answer, [], external_context, "MEDIUM"
                )

                return RAGstate(
                    question=state.question,
                    chat_history=state.chat_history,
                    mode=state.mode,
                    language=state.language,
                    reply_language=reply_language,
                    retrieved_docs=[],
                    answer=answer,
                    context_quality="INSUFFICIENT",
                    source_type="external",
                    confidence=confidence,
                    external_context=external_context,
                    escalations=escalations,
                    citations=citations
                )

            context = []

            for i, d in enumerate(docs, start=1):

                friendly = self._friendly_source(
                    d.metadata.get("source", "Unknown")
                )

                page = d.metadata.get("page", "N/A")

                context.append(
                    f"[Document {i} | Source: {friendly}, page {page}]\n{d.page_content}"
                )

            merged_context = "\n\n".join(context)

            context_quality = self.evaluate_context(
                rewritten_question,
                merged_context
            )

            print(f"Context Quality Decision: {context_quality}")

            if context_quality == "INSUFFICIENT":

                print("Using Tavily corrective search...")

                raw = self.external_search(rewritten_question)

                external_context, ext_sources = self._format_external(raw)

                answer = self.generate_corrective_answer(
                    rewritten_question,
                    external_context,
                    ext_sources,
                    state.mode,
                    reply_language,
                    lawyer_block
                )

                answer, citations, confidence = self._check_answer(
                    answer, docs, external_context, "MEDIUM"
                )

                return RAGstate(
                    question=state.question,
                    chat_history=state.chat_history,
                    mode=state.mode,
                    language=state.language,
                    reply_language=reply_language,
                    retrieved_docs=docs,
                    answer=answer,
                    context_quality="INSUFFICIENT",
                    source_type="external",
                    confidence=confidence,
                    external_context=external_context,
                    escalations=escalations,
                    citations=citations
                )

            answer = self.generate_rag_answer(
                rewritten_question,
                merged_context,
                state.mode,
                reply_language,
                lawyer_block
            )

            answer, citations, confidence = self._check_answer(
                answer, docs, "", "HIGH"
            )

            return RAGstate(
                question=state.question,
                chat_history=state.chat_history,
                mode=state.mode,
                language=state.language,
                reply_language=reply_language,
                retrieved_docs=docs,
                answer=answer,
                context_quality="SUFFICIENT",
                source_type="vectorstore",
                confidence=confidence,
                external_context="",
                escalations=escalations,
                citations=citations
            )

        except Exception as e:

            answer = f"Error: {str(e)}"
            if "rate_limit" in str(e) or "429" in str(e):
                # Groq free tier: shown to people instead of the raw API error.
                answer = (
                    "Nyaya.ai has hit its free daily usage limit on the AI model. "
                    "Please try again in a little while. (RATE_LIMIT)"
                )
            return RAGstate(
                question=state.question,
                chat_history=state.chat_history,
                mode=state.mode,
                language=state.language,
                reply_language=reply_language,
                retrieved_docs=[],
                answer=answer,
                context_quality="ERROR",
                source_type="system",
                confidence="LOW",
                external_context=""
            )