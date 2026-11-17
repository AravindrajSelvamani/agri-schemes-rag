# 🌾 AgriScheme AI — Beginner RAG Buildathon

An educational **Agricultural Government Schemes RAG** project with a colorful Streamlit UI, FastAPI backend, LangChain, OpenAI embeddings/chat and a persistent local FAISS index.

## Folder structure

```text
buildathon/
└── agri-schemes-rag/
    ├── frontend/
    │   ├── app.py               # Streamlit UI
    │   ├── style.css            # All UI styling changes go here
    │   └── requirements.txt
    ├── backend/
    │   ├── main.py              # FastAPI endpoints and both RAG pipelines
    │   ├── .env.example         # Copy to .env and add API key
    │   ├── requirements.txt
    │   └── data/
    │       ├── uploads/         # PDFs saved here
    │       └── faiss_index/     # index.faiss + index.pkl saved here
    ├── .gitignore
    └── README.md
```

## Setup on Windows (recommended Python 3.11 or 3.12)

**Terminal 1 — Backend:**

```powershell
cd buildathon\agri-schemes-rag\backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `backend/.env` and replace `sk-your-key-here` with your OpenAI API key. This API uses paid OpenAI services (embeddings + chat).

```powershell
uvicorn main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

**Terminal 2 — Frontend:**

```powershell
cd buildathon\agri-schemes-rag\frontend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

UI: http://localhost:8501

> Run each terminal from its respective `backend` or `frontend` folder. If `py -3.11` is not installed, install Python 3.11 or 3.12 first. Python 3.14 may cause wheel compatibility issues for some dependencies.

## Pipeline 1: Upload / Ingestion

```text
Streamlit PDF uploader
    → POST /upload
    → Save PDF to backend/data/uploads/
    → PyPDFLoader extracts pages
    → RecursiveCharacterTextSplitter creates chunks
    → OpenAIEmbeddings creates vectors
    → FAISS adds vectors and persists index.faiss + index.pkl
```

## Pipeline 2: Retrieval / Q&A

```text
Streamlit question
    → POST /ask
    → OpenAIEmbeddings embeds the question
    → FAISS similarity_search(k=4)
    → Retrieved text + question → ChatOpenAI
    → Answer and source PDF/page returned to UI
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Backend and FAISS index status |
| POST | `/upload` | Multipart PDF upload, parse, embed, save FAISS |
| POST | `/ask` | JSON `{ "question": "Who is eligible?" }` → answer + sources |

## Beginner testing checklist

1. Start backend and frontend; sidebar should say **Backend connected**.
2. Upload a **text-based** government schemes PDF (max 15 MB).
3. See page count and chunk count, and check `backend/data/uploads/` and `backend/data/faiss_index/`.
4. Ask a question answered by the PDF and inspect the cited source pages.
5. Ask something not in the PDF; the assistant should say the information is not found.
6. Restart backend and ask again: the FAISS index should persist.

## Notes and limitations

- **Use trusted PDFs only.** FAISS loads a local pickle metadata file; never replace the index files with untrusted files.
- This first version supports **text PDFs only**, not scanned/image-only PDFs (OCR can be added later).
- Uploading the same PDF again creates duplicate chunks; deduplication is a future enhancement.
- This is an educational document-search tool, **not an official government service**. Confirm scheme rules, eligibility, amounts and deadlines from official sources.
- This is a **local development app**, not production-hardened. Add authentication, rate limits, antivirus scanning and background processing before deploying publicly.
- To start with a fresh knowledge base, stop the backend and delete the generated files inside `backend/data/faiss_index/` (and optionally `backend/data/uploads/`).
