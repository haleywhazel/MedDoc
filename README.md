# MedDoc – AI HR Assistant for Hospitals

MedDoc is an end-to-end application that lets hospital staff ask HR-related questions in natural language and receive reliable answers sourced directly from the hospital’s official policy documents.

## Why?
Hospitals today often assign a full-time staff member to manually answer routine HR questions.  Most of these answers are already written in employee contracts or HR guidelines, but the documents are hard to navigate.  MedDoc automates this workflow with an AI chatbot that understands staff queries, searches the relevant documents, and produces accurate, reference-backed answers.

## High-Level Architecture
```
 ▼  Staff question                        
 ┌─────────────────────────────────────┐ 
 │           Next.js Front-end         │
 └─────────────────────────────────────┘ 
                │ REST / WebSocket
                ▼                       
 ┌─────────────────────────────────────┐ 
 │      FastAPI Back-end (Python)      │
 │  • /api/chat – retrieve answer      │
 │  • /api/health – healthcheck        │
 └─────────────────────────────────────┘ 
                │
                ▼
 ┌─────────────────────────────────────┐ 
 │  Retrieval + Generation Pipeline    │
 │  1. Vector search in ChromaDB       │
 │  2. Prompt LLM (Groq for dev)       │
 └─────────────────────────────────────┘ 
                │
                ▼
 ┌─────────────────────────────────────┐ 
 │         HR PDF Document Store       │
 └─────────────────────────────────────┘ 
```

## Technology
- **Backend**: Python, FastAPI
- **LLM**: Groq API (easily swappable)
- **Embeddings & Vector DB**: LangChain, OpenAI-compatible embeddings, ChromaDB (local persistent mode)
- **PDF Parsing**: PyMuPDF (`fitz`)
- **Front-end**: Next.js (React)

## Repository Layout
```
backend/              # FastAPI application and pipelines
  ├── main.py         # FastAPI app entry point
  ├── api/            # API routes (chat, health)
  ├── ingestion/      # Pre-processing (PDF → chunks → Chroma)
  └── retrieval/      # Helper to query Chroma and call an LLM
frontend/             # Next.js app (to be generated)
requirements.txt      # Python dependencies
```

## Quick Start (Backend Only)
1. Create & activate the `MedDoc` conda env (already done).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Put sample HR PDFs into a folder, e.g. `data/policies/`.
4. Pre-process PDFs and build / update the local Chroma vector store:
   ```bash
   # Option 1 – use built-in defaults (edit variables inside the script)
   python backend/ingestion/preprocess.py

   # Option 2 – point to a folder & YAML config
   # (see backend/ingestion/preprocess_config.yaml for an example)
   #
   #   • embedding_model / chroma_root
   #   • chunking parameters
   ```
5. Run the API:
   ```bash
   uvicorn backend.main:app --reload
   ```
6. `POST /api/chat` with `{"question": "What is the maternity leave policy?"}`.

The front-end will be added in a later step. 