from __future__ import annotations

import textwrap
from typing import List

from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import HumanMessage, SystemMessage
from langchain.vectorstores import Chroma

from backend.config import (CHROMA_PATH, OPENAI_API_KEY, OPENAI_MODEL,
                            require_env)

# ---------------------------------------------------------------------------
# Vector store helpers
# ---------------------------------------------------------------------------

def _get_vector_store() -> Chroma:
    """Open the persisted ChromaDB instance in read-only mode."""
    embeddings = OpenAIEmbeddings(openai_api_key=require_env("OPENAI_API_KEY", OPENAI_API_KEY))
    return Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_answer(question: str) -> str:
    """Return an answer to `question` using retrieval-augmented generation.

    1. Run similarity search in the local Chroma vector DB to fetch top-K chunks.
    2. Feed the chunks + question to the OpenAI chat model (gpt-3.5-turbo).
    """
    vectordb = _get_vector_store()
    docs = vectordb.similarity_search(question, k=4)

    # Combine documents into context
    context: str = "\n\n".join(d.page_content for d in docs)

    system_prompt = (
        "You are MedDoc, an HR assistant for hospital staff. "
        "Answer the user question based solely on the provided HR policy context. "
        "If the context does not contain the answer, reply that you do not know instead of inventing one."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=textwrap.dedent(f"""
            Context:
            {context}

            Question: {question}
        """)),
    ]

    llm = ChatOpenAI(
        model_name=OPENAI_MODEL,
        temperature=0.1,
        openai_api_key=require_env("OPENAI_API_KEY", OPENAI_API_KEY),
    )
    response = llm(messages)

    return response.content.strip() 