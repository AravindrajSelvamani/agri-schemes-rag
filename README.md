# 🌾 Agricultural Government Schemes RAG Chatbot

A beginner-friendly **Retrieval-Augmented Generation (RAG)** application for asking questions about agricultural government schemes using your own PDF documents.

**Frontend:** Streamlit + custom CSS  
**Backend:** Python + FastAPI + LangChain  
**Embeddings:** Hugging Face `sentence-transformers/all-MiniLM-L6-v2` (local CPU)  
**Vector database:** FAISS (saved to disk)  
**Answer generation:** OpenAI `ChatOpenAI` (requires API key)  
**Chat experience:** Sidebar PDF upload, conversational interface, streamed answers and PDF source references.

> **Important:** Answers are based on the uploaded PDFs, not a live government schemes database. Always verify scheme eligibility, dates and benefits with official government sources before making decisions.

## 1. Project folder structure

```text
buildathon/
└── agri-schemes-rag/
    ├── frontend/
    │   ├── app.py                    # Streamlit chatbot and sidebar upload
    │   ├── style.css                 # Custom colorful UI styles
    │   └── requirements.txt         # Streamlit and requests
    ├── backend/
    │   ├── main.py                   # FastAPI + LangChain RAG pipelines
    │   ├── requirements.txt         # Base backend dependencies
    │   ├── requirements-additions.txt # Hugging Face dependencies
    │   ├── .env.example              # Environment variable template
    │   ├── .env                      # Your local API key (create this; do not commit)
    │   └── data/
    │       ├── uploads/              # Saved uploaded PDFs
    │       └── faiss_index/          # index.faiss and index.pkl
    └── README.md
```

The `requirements-additions.txt` file is included in the chatbot update ZIP. Copy the updated `frontend/app.py`, `frontend/style.css`, `backend/main.py`, and `backend/requirements-additions.txt` into the matching folders of your original project. Keep the original requirements files.

## 2. Prerequisites

- Windows 10/11, PowerShell, VS Code or another editor
- **Python 3.11** recommended for easier package compatibility (Python 3.14 can cause installation issues)
- Internet access for installation, first Hugging Face model download, and OpenAI requests
- OpenAI API key with API billing configured
- Enough free disk space for Python dependencies, the embedding model, uploaded PDFs and FAISS indexes

Check Python:

```powershell
py -3.11 --version
```

If Python 3.11 is not installed, install it before proceeding. Commands below assume you extracted the project into a folder named `buildathon`.

## 3. Backend setup (PowerShell terminal 1)

Navigate to your project backend (adjust the path to your computer):

```powershell
cd buildathon\agri-schemes-rag\backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-additions.txt
Copy-Item .env.example .env
```

If PowerShell prevents activation, you can use `cmd.exe` with `.venv\Scripts\activate.bat`, or run `.venv\Scripts\python.exe` directly. Avoid changing system-wide execution policies unnecessarily.

Edit `backend/.env`:

```dotenv
OPENAI_API_KEY=your_openai_api_key_here
CHAT_MODEL=gpt-4o-mini
```

Do not put your real API key in source code or share your `.env` file.

Start FastAPI:

```powershell
uvicorn main:app --reload --port 8000
```

Open **http://127.0.0.1:8000/docs** for interactive Swagger API documentation.

## 4. Frontend setup (PowerShell terminal 2)

Open another terminal:

```powershell
cd buildathon\agri-schemes-rag\frontend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

By default the frontend calls `http://127.0.0.1:8000`. To override the backend URL in PowerShell before launching Streamlit:

```powershell
$env:BACKEND_URL="http://127.0.0.1:8000"
streamlit run app.py
```

## 5. How to use the chatbot

1. Open the Streamlit page.
2. In the **left sidebar**, select a government scheme PDF.
3. Click **Upload & Index**. The backend saves the PDF, extracts its text, splits it into chunks, generates Hugging Face embeddings and writes them to FAISS.
4. Wait for the success message showing the number of pages and chunks.
5. Ask a question in the **chat input**, such as: `Who is eligible for this scheme?`
6. Watch the answer appear progressively using `st.write_stream()`.
7. Expand **PDF Sources** below the answer to inspect the supporting filename, page number and excerpt.
8. Use **Clear chat** to reset the current Streamlit chat history (it does **not** delete PDFs or the FAISS index).

Example questions:

- What are the eligibility criteria for PM-KISAN according to my uploaded document?
- What benefits does this scheme provide?
- Which documents are needed to apply?
- How does a farmer apply for this scheme?
- Explain the scheme in Tamil.

**Tanglish:** Sidebar-la PDF upload pannunga. Upload & Index click panna, PDF text chunks-ah split aagi Hugging Face embedding create aagum. FAISS-la save aagum. Apram chat-la question ketta relevant chunks retrieve panni ChatOpenAI answer stream pannum.

## 6. Pipeline 1 — PDF ingestion

```text
Streamlit sidebar (PDF upload)
        ↓ POST /upload
FastAPI validates PDF (max 15 MB)
        ↓
Save PDF → backend/data/uploads/
        ↓
PyPDFLoader: extract page text
        ↓
RecursiveCharacterTextSplitter
  chunk_size=900, chunk_overlap=150
        ↓
HuggingFaceEmbeddings
  sentence-transformers/all-MiniLM-L6-v2
  CPU; normalized 384-dimensional vectors
        ↓
FAISS.from_documents() or add_documents()
        ↓
Persist → backend/data/faiss_index/
  index.faiss + index.pkl
```

The first use downloads the Hugging Face model. Later runs can reuse its local cache. Embedding creation does not require an OpenAI key.

**Limitations:** This version extracts embedded PDF text; scanned/image-only PDFs need OCR (not included). Uploading the same document twice can create duplicate indexed chunks. The backend currently maintains a shared index across uploads, not separate user-specific knowledge bases.

## 7. Pipeline 2 — Question answering with streaming

```text
User types a question in st.chat_input()
        ↓ POST /ask/stream
FastAPI loads the existing FAISS index
        ↓
Hugging Face embeds the question
        ↓
FAISS similarity_search(question, k=4)
        ↓
Retrieve relevant PDF excerpts and source metadata
        ↓
LangChain prompt + ChatOpenAI (gpt-4o-mini by default)
        ↓
Model streams response chunks
        ↓
FastAPI StreamingResponse (NDJSON)
        ↓
Streamlit st.write_stream()
        ↓
Chat answer + expandable PDF Sources
```

The chatbot keeps conversation **display history** in Streamlit session state. The current backend sends only the **latest question and retrieved excerpts** to the model, so it does not yet support context-aware follow-up questions that depend on earlier turns.

## 8. API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Backend status, number of stored PDFs, whether an index exists |
| POST | `/upload` | Upload a PDF as multipart field `file`, save it, and index its text |
| POST | `/ask` | Ask a question and receive a complete JSON answer with sources |
| POST | `/ask/stream` | Ask a question and receive streamed newline-delimited JSON events |

Example health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Example non-streaming question (after uploading a PDF):

```powershell
$body = @{ question = "What are the eligibility criteria?" } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/ask -Method Post -ContentType "application/json" -Body $body
```

`/ask/stream` sends NDJSON events with types `sources`, `token`, `done`, or `error`. The Streamlit UI parses them and progressively renders `token` content.

## 9. Switching from old OpenAI embeddings to Hugging Face

**Very important:** If you created a FAISS index with OpenAI embeddings in the original project, it cannot be reused with the new 384-dimensional Hugging Face embeddings.

1. Stop the backend and frontend.
2. Delete **only** `backend/data/faiss_index/index.faiss` and `backend/data/faiss_index/index.pkl` from your old index.
3. Keep PDFs in `backend/data/uploads/` if you need them, but the current app does **not** automatically re-index files from that directory.
4. Restart both applications and **upload the PDFs again from the sidebar**.

**Security:** FAISS's saved metadata uses Python pickle. Load only index files generated by your own trusted application; never copy unknown `index.pkl` files into the index folder.

## 10. Troubleshooting

| Issue | What to check |
|---|---|
| `ModuleNotFoundError` | Activate the correct virtual environment and install both backend requirements files |
| `uvicorn` not recognized | Run `python -m uvicorn main:app --reload --port 8000` from `backend/` |
| Backend offline in sidebar | Confirm FastAPI is running on port 8000 and `BACKEND_URL` is correct |
| `OPENAI_API_KEY is missing` | Create `backend/.env`, add a valid key and restart FastAPI |
| Slow first upload | The Hugging Face model may be downloading or initializing on CPU |
| FAISS dimension mismatch | Remove the old OpenAI-embedding index files and re-upload PDFs |
| No text extracted from PDF | The PDF may be scanned; this version has no OCR |
| Stream fails | Check FastAPI terminal errors, API key, internet and API billing |
| Chat disabled | Backend must be online and at least one PDF must be indexed |
| `zstandard`/wheel build error | Use a clean Python 3.11 environment rather than Python 3.14 |

## 11. What costs money?

- **Streamlit:** free when running locally.
- **FastAPI / LangChain / FAISS:** open-source, running locally.
- **Hugging Face embeddings:** local CPU inference; no embedding API charge, but uses RAM/CPU and downloads model files.
- **ChatOpenAI:** OpenAI API calls are billed separately according to your account and chosen model.

## 12. Current MVP limitations and next improvements

This is a **local learning MVP**, not a production-ready government advisory service. The application currently lacks authentication, user-specific storage, duplicate document detection, automatic OCR, document deletion, robust rate limiting, and full conversation-aware retrieval. Do not expose the backend publicly without adding appropriate security controls.

Good next steps:

1. Add a document list and delete/re-index options.
2. Add multilingual Tamil question/answer testing.
3. Add OCR for scanned scheme PDFs.
4. Add chat history-aware question rewriting.
5. Add official government source URLs and document freshness checks.
6. Add automated tests and deployment configuration.

---

**Beginner milestone:** Upload one text-based agricultural scheme PDF, confirm the FAISS files are created, ask a question, watch the streamed answer, and verify the cited PDF page yourself.
