import os
import pathlib
from typing import List
import fitz  # PyMuPDF
import chromadb
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

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
            metadata = {
                "filename": pdf_path.name,
                "page_number": None,
                "chunk": i
            }
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

    client = chromadb.HttpClient(host=os.getenv("CHROMA_HOST", "localhost"), port=int(os.getenv("CHROMA_PORT", "8000")))
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    vectordb = Chroma(client=client, collection_name="documents", embedding_function=embeddings)

    batch_size = 100
    total_docs = len(docs)

    for i in range(0, total_docs, batch_size):
        batch_docs = list(docs[i:i+batch_size])
        batch_metas = list(metadatas[i:i+batch_size])

        print(f"Processing batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size}")
        vectordb.add_texts(texts=batch_docs, metadatas=batch_metas)

    print(f"Ingested {len(docs)} chunks into ChromaDB collection")

if __name__ == "__main__":
    ingest_documents("/app/local/shrewsbury_policies")
