from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, List

import chromadb
import yaml
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm
from unstructured.chunking.title import chunk_by_title
from unstructured.documents.elements import Element
from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import elements_from_json, elements_to_json

_DEFAULT_CFG: dict[str, Any] = {
    "partition_strategy": "hi_res",
    "save_elements": True,
    "save_folder": "cache/partitioned_elements/hi_res",
    "chunking": {
        "strategy": "by_title",
        "max_characters": 1000,
        "combine_text_under_n_chars": 500,
        "multipage_sections": True,
        "overlap": 200,
    },
    "chroma": {
        "embedding_model": "text-embedding-3-large",
        "collection_name": "documents",
    },
}

def _cache_path(pdf_path: Path, save_folder: Path) -> Path:
    save_folder.mkdir(parents=True, exist_ok=True)
    return save_folder / f"{pdf_path.stem}.json"

def preprocess_pdf(pdf_path: Path, cfg: dict[str, Any]) -> List[Element]:
    save_folder = Path("/app") / cfg["save_folder"]
    cache_file = _cache_path(pdf_path, save_folder)

    if cfg.get("save_elements", False) and cache_file.exists():
        print(f"Loading cached elements from {cache_file}")
        return elements_from_json(cache_file)

    print(f"Partitioning PDF: {pdf_path.name}")
    elements = partition_pdf(filename=str(pdf_path), strategy=cfg["partition_strategy"])

    if cfg.get("save_elements", False):
        elements_to_json(elements, cache_file)

    return elements

def chunk_elements(elements: List[Element], cfg: dict[str, Any]):
    c_cfg = cfg["chunking"]
    strategy = c_cfg["strategy"]

    if strategy != "by_title":
        raise NotImplementedError(f"Chunking strategy '{strategy}' is not supported yet.")

    chunks = chunk_by_title(
        elements,
        max_characters=c_cfg["max_characters"],
        combine_text_under_n_chars=c_cfg["combine_text_under_n_chars"],
        multipage_sections=c_cfg["multipage_sections"],
        overlap=c_cfg["overlap"],
    )

    return chunks

def process_folder(folder: Path, cfg: dict[str, Any]) -> None:
    pdf_files = sorted(folder.glob("*.pdf"))
    if not pdf_files:
        print(f"[preprocess] No PDF files found in {folder}")
        return

    print(f"[preprocess] Found {len(pdf_files)} PDF files")

    chroma_host = os.getenv("CHROMA_HOST", "localhost")
    chroma_port = int(os.getenv("CHROMA_PORT", "8000"))

    print(f"[preprocess] Connecting to ChromaDB at {chroma_host}:{chroma_port}")
    client = chromadb.HttpClient(host=chroma_host, port=chroma_port)

    chroma_cfg = cfg.get("chroma", {})
    embedding_model: str = chroma_cfg["embedding_model"]
    collection_name: str = chroma_cfg["collection_name"]

    embeddings = OpenAIEmbeddings(
        model=embedding_model,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    vectordb = Chroma(
        client=client,
        collection_name=collection_name,
        embedding_function=embeddings
    )

    total_chunks = 0

    def _compute_hash(path: Path) -> str:
        sha = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def _pdf_embedding_exists(collection, pdf_hash: str) -> bool:
        try:
            res = collection.get(where={"pdf_hash": pdf_hash}, limit=1, include=["metadatas"])
            return bool(res and res.get("ids"))
        except Exception:
            return False

    for pdf_path in tqdm(pdf_files, desc="Processing PDFs", unit="pdf"):
        pdf_hash = _compute_hash(pdf_path)

        if _pdf_embedding_exists(vectordb._collection, pdf_hash):
            print(f"[preprocess] Skipping {pdf_path.name} - already processed")
            continue

        elements = preprocess_pdf(pdf_path, cfg)
        chunks = chunk_elements(elements, cfg)
        if not chunks:
            print(f"[preprocess] Warning: No chunks found for {pdf_path}")
            continue

        texts: list[str] = []
        metadatas: list[dict[str, Any]] = []
        ids: list[str] = []

        for idx, chunk in enumerate(chunks):
            texts.append(chunk.text)
            meta = chunk.metadata.to_dict()
            metadatas.append(
                {
                    "filename": meta.get("filename", pdf_path.name),
                    "page_number": meta.get("page_number"),
                    "pdf_hash": pdf_hash,
                }
            )
            ids.append(f"{pdf_hash}-{idx}")

        vectordb.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        total_chunks += len(texts)
        print(f"[preprocess] Added {len(texts)} chunks from {pdf_path.name}")

    print(f"[preprocess] COMPLETED: Added {total_chunks} total chunks to ChromaDB")

def load_config(default_cfg: dict, config_path: str | None = None) -> dict:
    cfg = default_cfg.copy()
    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            user_cfg = yaml.safe_load(f)
            cfg.update(user_cfg)
    return cfg

def main() -> None:
    """Run the pre-processing pipeline without relying on CLI arguments.

    Edit the *pdfs_dir* and *config_path* variables below to match your
    environment.  The function can still be called programmatically from other
    modules.
    """
    pdfs_dir: Path = Path("/app/local/shrewsbury_policies")

    config_path: str | None = None  # or a YAML file path

    cfg = load_config(_DEFAULT_CFG, config_path)
    process_folder(pdfs_dir, cfg)

if __name__ == "__main__":
    main()
