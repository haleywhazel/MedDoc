import argparse
import pathlib
from typing import List

import fitz  # PyMuPDF
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma

CHROMA_PATH = "chroma_db"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def extract_text_from_pdf(pdf_path: pathlib.Path) -> str:
    """Read full text from a PDF using PyMuPDF."""
    doc = fitz.open(pdf_path)
    text = "".join(page.get_text() for page in doc)
    return text


def load_documents(doc_dir: pathlib.Path) -> List[tuple[str, dict]]:
    """Return list of (chunk_text, metadata) tuples for all PDFs in a directory."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    texts = []
    for pdf_path in doc_dir.glob("*.pdf"):
        raw_text = extract_text_from_pdf(pdf_path)
        chunks = splitter.split_text(raw_text)
        for i, chunk in enumerate(chunks):
            metadata = {"source": str(pdf_path), "chunk": i}
            texts.append((chunk, metadata))
    return texts


def ingest_documents(doc_dir: str) -> None:
    """Parse PDFs, embed chunks, and persist them to Chroma DB."""
    dir_path = pathlib.Path(doc_dir)
    pairs = load_documents(dir_path)
    if not pairs:
        print("No PDF files found in", dir_path)
        return

    docs, metadatas = zip(*pairs)
    embeddings = OpenAIEmbeddings()
    Chroma.from_texts(
        list(docs),
        embeddings,
        metadatas=list(metadatas),
        persist_directory=CHROMA_PATH,
    ).persist()
    print(f"Ingested {len(docs)} chunks and stored them in {CHROMA_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest HR policy PDFs into ChromaDB.")
    parser.add_argument("--docs_dir", required=True, help="Path to directory containing PDF files")
    args = parser.parse_args()
    ingest_documents(args.docs_dir) 