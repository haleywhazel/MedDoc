from __future__ import annotations

"""Retrieval-augmented generator for MedDoc.

This module wraps three concerns:
1. Fetching relevant chunks from the local Chroma vector store.
2. Calling the chosen LLM with the chunks + user question.
3. (Optional) capturing a *trace* of the whole interaction so that
   we can evaluate the pipeline later on.

The public entry-point is :func:`get_answer`.
"""

import chromadb
import json
import os
import re
import textwrap
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from langchain.chat_models import init_chat_model
from langchain.schema import HumanMessage, SystemMessage
from langchain.vectorstores import Chroma
from langchain_core.messages.utils import count_tokens_approximately
from langchain_openai import OpenAIEmbeddings

from backend import ROOT_DIR
from backend.config import (CHROMA_PATH, OPENAI_API_KEY, OPENAI_MODEL,
                            require_env)
from backend.utils.config_utils import load_config

# ---------------------------------------------------------------------------
# Configuration helpers (mirrors backend/ingestion/preprocess.py style)
# ---------------------------------------------------------------------------

_DEFAULT_CFG: Dict[str, Any] = {
    "chroma": {"persist_dir": CHROMA_PATH},
    "embedding_model": "text-embedding-3-large",
    "top_k": 4,
    "llm": {"model": OPENAI_MODEL},
    "enable_tracing": True,
    "trace_path": "local/traces/query_traces.jsonl",
}

# ---------------------------------------------------------------------------
# Tracing utilities
# ---------------------------------------------------------------------------


@dataclass
class QueryTrace:
    """Container for everything we need to evaluate an answer."""

    question: str
    retrieved_docs: List[Dict[str, Any]]
    prompt: str
    raw_llm_response: str
    final_answer: str
    num_tokens: int
    ts: str = datetime.utcnow().isoformat()


def _persist_trace(trace: QueryTrace, cfg: Dict[str, Any]) -> None:
    """Append *trace* as a JSON-line to the configured file."""
    path = ROOT_DIR / cfg["trace_path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        json.dump(asdict(trace), fh, ensure_ascii=False)
        fh.write("\n")


# ---------------------------------------------------------------------------
# Vector store helpers
# ---------------------------------------------------------------------------


def _get_vector_store(cfg: Dict[str, Any]) -> Chroma:
    """Open the persisted ChromaDB instance in read-only mode."""
    embeddings = OpenAIEmbeddings(
        model=cfg["embedding_model"],
        openai_api_key=require_env("OPENAI_API_KEY", OPENAI_API_KEY),
    )

    client = chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", "8000"))
    )

    return Chroma(
        client=client,
        collection_name="documents",
        embedding_function=embeddings
    )

# ---------------------------------------------------------------------------
# Chat history formatting
# ---------------------------------------------------------------------------

def _format_chat_history(history):
    """Format the message history into a readable context string."""
    if not history:
        return ""

    formatted = []
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            formatted.append(f"User: {content}")
        else:
            formatted.append(f"Assistant: {content}")

    return "\n".join(formatted)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_answer(
    question: str,
    *,
    history: list[dict] | None = None,
    trace: bool = False,
    cfg_path: str | Path | None = None,
) -> str | Tuple[str, Dict[str, Any]]:
    """Return an answer to *question* using retrieval-augmented generation.

    Parameters
    ----------
    question: str
        End-user question.
    trace: bool, default False
        If *True* the function returns a `(answer, trace_dict)` tuple and also
        records the trace to disk.  If *False*, tracing depends solely on the
        configuration key `enable_tracing`.
    cfg_path: Optional[str | Path]
        Path to a YAML file whose contents will override the default config.
    """

    # return "Temporary answer: Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."

    cfg = load_config(_DEFAULT_CFG, cfg_path)

    # 1. Retrieve similar chunks
    vectordb = _get_vector_store(cfg)
    docs = vectordb.similarity_search(question, k=cfg["top_k"])

    if len(docs) == 0:
        no_info_msg = "I couldn't find the relevant information."
        if trace:
            return no_info_msg, [], {}
        return no_info_msg, []
    print(docs)

    # 2. Build prompt
    context_texts = [
        [
            f"Document: {doc.metadata['filename']}, Page: {doc.metadata.get('page_number', 'unknown')}",
            f"Content: {doc.page_content}",
        ]
        for doc in docs
    ]

    context = "\n\n".join(f"{doc[0]}\n{doc[1]}" for doc in context_texts)

    system_prompt = (
        "You are an HR assistant for NHS staff. "
        "Answer the question using ONLY the information in the provided context. "
        "You will be given conversation history for context, but always base your answers on the document context provided.\n\n"
        "Before answering:\n"
        "- Consider the conversation history to understand what the user is asking about.\n"
        "- If the question is too vague or ambiguous to answer accurately, ask the user for clarification. "
        "For example, if they ask 'What's the leave policy?' without specifying which type of leave, "
        "ask them to specify (e.g., annual leave, sick leave, maternity leave, adoption leave, etc.).\n"
        "- If the question is clear but the context is insufficient, reply 'I couldn't find relevant information in the available documents.' "
        "and do not add invented facts.\n\n"
        "Core behaviour rules:\n\n"
        "1. Evidence-only answers\n"
        "   - Only use the information found in the provided documents (context chunks).\n"
        "   - Never rely on prior knowledge or outside information.\n"
        "   - If nothing relevant is found, reply: 'I couldn't find relevant information in the available documents.'\n"
        "   - Do not speculate, guess, or paraphrase information that does not exist in the text.\n\n"
        "2. Clarify-first logic\n"
        "   - Before answering, check if the user's question is specific enough to locate an answer.\n"
        "   - If it is vague (e.g. 'What is my pay?', 'What leave do I get?', 'How many hours do I work?'), do NOT attempt to answer.\n"
        "   - Instead, ask 1–3 clarifying questions to narrow the topic, such as:\n"
        "     • 'Do you mean basic pay, enhanced pay, or sick pay?'\n"
        "     • 'Are you asking about maternity, paternity, or annual leave?'\n"
        "     • 'Which staff group or pay band are you referring to?'\n"
        "   - Always ask for only the minimum extra details required to answer accurately.\n\n"
        "3. Citation discipline\n"
        "   - Every statement in your answer must be traceable to at least one document.\n"
        "   - Provide citations for each supporting document and, if available, the page or section.\n"
        "   - If no document supports a point, do NOT include it.\n\n"
        "4. Tone and style\n"
        "   - Use plain, concise English suitable for NHS staff.\n"
        "   - Prefer bullet points where appropriate.\n"
        "   - Avoid excessive legal or policy jargon unless quoting directly.\n"
        "   - Never include disclaimers about being an AI assistant.\n\n"
        "Output format – critical for parsing:\n\n"
        "If you provide an answer (not a clarification question), add a single blank line followed by a JSON object "
        "*on a single line* with the key 'sources'. "
        "Note that the sources MUST come from the context, and not generated or made up. "
        "The sources must also be relevant to the answer that you provided. "
        "The value of 'sources' must be an array of objects, each having: \n"
        "  • file  – the document name (string)\n"
        "  • page  – page number as an integer (omit if unknown)\n\n"
        "Example of a complete answer:\n"
        "Employees are entitled to take 52 weeks' adoption leave. …\n\n"
        '{"sources":[{"file":"Policy-Handbook.pdf","page":37}]}\n\n'
        "Example of asking for clarification (no sources needed):\n"
        "Could you please specify which type of leave you're asking about? "
        "For example: annual leave, sick leave, maternity leave, or adoption leave?\n"
    )

    prompt_content = textwrap.dedent(
        f"""
        Context:
        {context}

        {f'''
        Previous Conversation:
        {_format_chat_history(history)}
        ''' if history else ''}

        Current Question: {question}
        """
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt_content),
    ]

    # 3. Call LLM
    model = init_chat_model(
        OPENAI_MODEL,
        model_provider="openai",
        api_key=OPENAI_API_KEY,
    )
    response = model.invoke(messages)

    raw_response: str = response.content.strip()

    answer, sources = _extract_answer_and_sources(raw_response)

    # ---------------------------------------------------------------------
    # Tracing (optional)
    # ---------------------------------------------------------------------
    should_trace = trace or cfg.get("enable_tracing", False)
    trace_dict: Dict[str, Any] | None = None
    if should_trace:
        retrieved_docs_meta = [
            {"page_content": d.page_content, "metadata": d.metadata} for d in docs
        ]
        q_trace = QueryTrace(
            question=question,
            retrieved_docs=retrieved_docs_meta,
            prompt=f"{system_prompt}\n\n{prompt_content}",
            raw_llm_response=response.content,
            final_answer=answer,
            num_tokens=count_tokens_approximately(messages),
        )
        _persist_trace(q_trace, cfg)
        trace_dict = asdict(q_trace)

    if trace:
        return answer, sources, trace_dict
    return answer, sources


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _extract_answer_and_sources(raw_response: str) -> tuple[str, List[Dict[str, Any]]]:
    """Split *raw_response* into natural-language answer and sources array.

    The model is expected to append a single-line JSON object like::

        {"sources":[{"file":"Policy.pdf","page":3}]}
    """

    json_match = re.search(r"\{.*\}\s*$", raw_response, re.DOTALL)
    sources: list[dict[str, Any]] = []
    if json_match:
        sources_obj = json.loads(json_match.group(0))
        sources = sources_obj.get("sources", []) if isinstance(sources_obj, dict) else []
        answer_part = raw_response[: json_match.start()].strip()
    else:
        answer_part = raw_response.strip()

    return answer_part, sources
