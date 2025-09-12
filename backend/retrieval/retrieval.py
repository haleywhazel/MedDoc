from __future__ import annotations

"""Retrieval-augmented generator for MedDoc.

This module wraps three concerns:
1. Fetching relevant chunks from the local Chroma vector store.
2. Calling the chosen LLM with the chunks + user question.
3. (Optional) capturing a *trace* of the whole interaction so that
   we can evaluate the pipeline later on.

The public entry-point is :func:`get_answer`.
"""

import json
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
    "top_k": 6,
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
    return Chroma(
        persist_directory=f"{cfg['chroma']['persist_dir']}/{cfg['embedding_model']}",
        embedding_function=embeddings,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_answer(
    question: str,
    *,
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
        return "I couldn't find the relevant information."
    print(docs)

    # 2. Build prompt
    context_texts = [
        [
            f"Document: {doc.metadata['filename']}, Page: {doc.metadata['page_number']}",
            f"Content: {doc.page_content}",
        ]
        for doc in docs
    ]

    context = "\n\n".join(f"{doc[0]}\n{doc[1]}" for doc in context_texts)

    system_prompt = (
        "You are an HR assistant for NHS staffs."
        "Answer the question based solely on the provided policy context, if multiple documents are relevant, provide a summary of relevant information."
        "If the context does not contain the answer, reply 'I couldn't find the relevant information.' instead of inventing one."
        "For example, if the document name seems irrelevant to the question, or if the given context looks like some kind of form, do not use it to answer."
        "Please state the answer by adhering closely to the original text, and do not generate any additional information."
        "If sensible, provide users with some extra information that is useful, note that this also has to be based on the context ONLY."
        "At the end of your answer, cite the page number and document name of the text that you used to answer the question."
    )

    prompt_content = textwrap.dedent(
        f"""
        Context:
        {context}

        Question: {question}
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
    answer: str = response.content.strip()

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

    return (answer, trace_dict) if trace else answer
