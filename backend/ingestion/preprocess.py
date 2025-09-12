from __future__ import annotations

"""Utility to partition HR policy PDFs and (optionally) chunk them.

Why is this a separate script?
------------------------------
Partitioning a PDF page-by-page with the *unstructured* library is slow (OCR
and layout detection).  To avoid repeating that cost every time we tweak the
chunking parameters we:

1. **Cache** the raw `Element` objects produced by `partition_pdf()` in a JSON
   file that lives next to the source PDF.
2. Re-run *only* the chunking step when we want to experiment with new
   `max_characters`, `overlap`, … values.

The behaviour is controlled by a small YAML file so we do *not* have to change
code when we want to try a different partition strategy (e.g. "ocr_only") or a
new chunking policy (e.g. by AI-generated sections).
"""

import hashlib
from pathlib import Path
from typing import Any, List

import yaml
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm
from unstructured.chunking.title import chunk_by_title
from unstructured.documents.elements import Element
from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import elements_from_json, elements_to_json

from backend import ROOT_DIR
from backend.config import OPENAI_API_KEY, require_env
from backend.utils.config_utils import load_config

# ---------------------------------------------------------------------------
# Default configuration.  If a YAML file is supplied it will *override* these
# keys (we merge, not replace, so you can omit values you do not want to
# change).
# ---------------------------------------------------------------------------
_DEFAULT_CFG: dict[str, Any] = {
    "partition_strategy": "hi_res",
    "save_elements": True,
    "save_folder": "local/partitioned_elements/hi_res",
    "chunking": {
        "strategy": "by_title",  # currently the only implemented option
        "max_characters": 1000,
        "combine_text_under_n_chars": 500,
        "multipage_sections": True,
        "overlap": 200,
    },
    "chroma": {
        "embedding_model": "text-embedding-3-large",
        "chroma_root": "chroma_langchain_db",
    },
}

# ---------------------------------------------------------------------------
# Core pipeline steps
# ---------------------------------------------------------------------------


def _cache_path(pdf_path: Path, save_folder: Path) -> Path:
    """Return JSON cache file path for *pdf_path* inside *save_folder*."""
    save_folder.mkdir(parents=True, exist_ok=True)
    return save_folder / f"{pdf_path.stem}.json"


def preprocess_pdf(pdf_path: Path, cfg: dict[str, Any]) -> List[Element]:
    """Partition a single PDF and return a list of *unstructured* Elements.

    If caching is enabled the function first looks for an existing JSON cache
    and re-uses it if present.
    """
    save_folder = ROOT_DIR / cfg["save_folder"]
    cache_file = _cache_path(pdf_path, save_folder)

    if cfg.get("save_elements", False) and cache_file.exists():
        # print(f"Loading cached elements from {cache_file}")
        return elements_from_json(cache_file)

    elements = partition_pdf(filename=str(pdf_path), strategy=cfg["partition_strategy"])

    if cfg.get("save_elements", False):
        elements_to_json(elements, cache_file)

    return elements


def chunk_elements(elements: List[Element], cfg: dict[str, Any]):
    """Chunk a list of Elements according to the chosen strategy.

    Only `by_title` is implemented for now.  It returns a list of chunk Elements
    (same *unstructured* data class).  Persisting the chunks is *out of scope*
    for this function but can be added easily later on.
    """
    c_cfg = cfg["chunking"]
    strategy = c_cfg["strategy"]

    if strategy != "by_title":
        raise NotImplementedError(f"Chunking strategy '{strategy}' is not supported yet.")

    if strategy == "by_title":
        chunks = chunk_by_title(
            elements,
            max_characters=c_cfg["max_characters"],
            combine_text_under_n_chars=c_cfg["combine_text_under_n_chars"],
            multipage_sections=c_cfg["multipage_sections"],
            overlap=c_cfg["overlap"],
        )

    return chunks


def process_folder(folder: Path, cfg: dict[str, Any]) -> None:
    """Partition + chunk all PDFs in *folder*, then persist chunks to Chroma."""

    pdf_files = sorted(folder.glob("*.pdf"))
    if not pdf_files:
        print(f"[preprocess] No PDF files found in {folder}")
        return

    # ------------------------------------------------------------------
    # Prepare embeddings + Chroma path from config (nested under "chroma")
    # ------------------------------------------------------------------
    chroma_cfg = cfg.get("chroma", {})
    embedding_model: str = chroma_cfg["embedding_model"]
    embeddings = OpenAIEmbeddings(
        model=embedding_model,
        api_key=require_env("OPENAI_API_KEY", OPENAI_API_KEY),
    )

    chroma_root = ROOT_DIR / chroma_cfg["chroma_root"]
    chroma_path = chroma_root / embedding_model.replace("/", "_")
    chroma_path.mkdir(parents=True, exist_ok=True)

    # Create / load the persistent Chroma vector store *once*
    vectordb = Chroma(persist_directory=str(chroma_path), embedding_function=embeddings)

    total_chunks = 0

    def _compute_hash(path: Path) -> str:
        """SHA256 of the file contents (as hex string)."""
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
            # Skip PDFs whose chunks are already stored for this embedding model
            print("skipping preprocess because it already exists")
            continue

        elements = preprocess_pdf(pdf_path, cfg)
        chunks = chunk_elements(elements, cfg)
        if not chunks:
            raise ValueError(f"No chunks found for {pdf_path}")

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

    print(f"[preprocess] Added {total_chunks} chunks to {chroma_path}")


def main() -> None:
    """Run the pre-processing pipeline without relying on CLI arguments.

    Edit the *pdfs_dir* and *config_path* variables below to match your
    environment.  The function can still be called programmatically from other
    modules.
    """
    pdfs_dir: Path = Path(ROOT_DIR) / "local" / "shrewsbury_policies"

    config_path: str | None = None  # or a YAML file path

    cfg = load_config(_DEFAULT_CFG, config_path)
    process_folder(pdfs_dir, cfg)


if __name__ == "__main__":
    main()
