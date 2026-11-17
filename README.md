# Agricultural Schemes RAG Assistant

A local chatbot for exploring Indian agricultural government scheme PDFs. Upload a text-based PDF, ask a question, and review the retrieved excerpts and page references alongside the answer.

Answers are generated from uploaded documents, not a live government database. Verify eligibility, benefits, deadlines, and other important details against current official sources.

## Features

- Upload and index multiple PDFs in a shared local knowledge base.
- Ask questions through a Streamlit chat interface and receive streamed answers.
- Inspect retrieved PDF filenames, page numbers, and excerpts.
- Generate embeddings locally with Hugging Face and store them in FAISS.
- Use OpenAI to generate answers from the retrieved excerpts, with a prompt requesting the language of the question where possible.

## Technology

| Component | Technology |
| --- | --- |
| Frontend | Streamlit, custom CSS, Requests |
| API | FastAPI, Uvicorn |
| PDF processing and retrieval | LangChain, PyPDF, FAISS |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` on CPU |
| Answer generation | OpenAI via LangChain (`gpt-4o-mini` by default) |

## Project structure

```text
agri-schemes-rag/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── data/
│       ├── uploads/          # Uploaded PDFs
│       └── faiss_index/      # Persisted FAISS index and metadata
├── frontend/
│   ├── app.py
│   ├── style.css
│   └── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.11 recommended.
- An OpenAI API key with access to the configured chat model and API billing.
- Internet access to install packages, download the embedding model on first use, and call OpenAI.
- A text-based PDF of 150 MB or less. Scanned PDFs require OCR, which is not included.

## Setup and run on Windows

The following commands assume PowerShell is open in the `agri-schemes-rag` folder. Use two terminals: one for the backend and one for the frontend.

### 1. Start the backend

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create `backend/.env` with your own credentials:

```dotenv
OPENAI_API_KEY=your_openai_api_key_here
CHAT_MODEL=gpt-4o-mini
```

`CHAT_MODEL` is optional. Keep your API key private and do not commit `.env`.

```powershell
python -m uvicorn main:app --reload --port 8000
```

The API runs at `http://127.0.0.1:8000`; interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 2. Start the frontend

In a second PowerShell terminal, from the project folder:

```powershell
cd frontend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open `http://localhost:8501`. The frontend connects to `http://127.0.0.1:8000` by default. To use another backend URL, set it before starting Streamlit:

```powershell
$env:BACKEND_URL = "http://127.0.0.1:8000"
python -m streamlit run app.py
```

If PowerShell blocks virtual environment activation, use the environment's Python directly, for example `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`, and use the same Python executable to start the service.

## Use the assistant

1. Start both services and open the Streamlit page.
2. Select a text-based government scheme PDF in the sidebar and click **Upload & Index**. The first upload may take longer while the embedding model downloads.
3. Once the index is ready, ask a question such as “What are the eligibility criteria?” or “Which documents are required to apply?”
4. Expand **PDF Sources** under the answer to check the retrieved pages and excerpts.
5. Use **Clear chat** to clear the displayed conversation. This does not delete uploaded PDFs or the index.


## How it works

1. The backend saves the PDF, extracts page text, and splits it into chunks of 900 characters with 150 characters of overlap.
2. The local embedding model converts chunks into vectors. FAISS stores them in `backend/data/faiss_index/`; subsequent uploads are added to the same index.
3. For each question, FAISS retrieves up to four similar chunks. The backend sends those excerpts and the question to the configured OpenAI chat model.
4. The frontend streams the response and shows the retrieved sources. Sources are retrieval results and should be checked against the original PDF.

Chat messages are retained in the Streamlit session for display, but prior turns are not sent to the backend. Follow-up questions should include the necessary context.

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health` | Reports status, uploaded PDF count, and whether an index exists. |
| POST | `/upload` | Uploads and indexes a PDF using multipart field `file`. |
| POST | `/ask` | Accepts a JSON question and returns an answer and sources. |
| POST | `/ask/stream` | Streams newline-delimited JSON source, token, completion, or error events. |

Questions must contain 3–2,000 characters. For example, after indexing a PDF:

```powershell
$body = @{ question = "What are the eligibility criteria?" } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/ask -Method Post -ContentType "application/json" -Body $body
```

## Limitations and troubleshooting

- **Backend offline:** Start FastAPI and check `BACKEND_URL` and port 8000.
- **Missing API key or answer failure:** Check `backend/.env`, model access, billing, and internet connectivity, then restart the backend after changing configuration.
- **No extractable text:** Use a text-based PDF; image-only scans need OCR.
- **Upload rejected:** Confirm the file is a valid PDF and no larger than 150 MB.
- **Import errors:** Install the appropriate requirements file in each service's environment. Python 3.11 is recommended if package installation fails.
- **Index compatibility:** Existing FAISS indexes must use the same embedding model and dimensions. To rebuild an incompatible index, stop the backend, remove the index files in `backend/data/faiss_index/`, restart it, and upload the PDFs again. Saved PDFs are not automatically re-indexed.

The app uses a shared local index, has no authentication or document deletion interface, and may index duplicate uploads. FAISS metadata uses pickle: only load index files created by a trusted source. This is a learning MVP and needs additional security and access controls before public deployment.

Local embeddings use CPU and disk space but do not incur an embedding API charge. OpenAI answer generation may incur API charges.
