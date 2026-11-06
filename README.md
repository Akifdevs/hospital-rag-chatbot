# Service RAG — Setup Guide

A strict documentation-grounded RAG (Retrieval-Augmented Generation) API with a chat widget frontend. The system only answers questions when it can confidently ground the answer in the indexed documentation — otherwise it refuses rather than guesses.

---

## Project Structure

```
Service-RAG-main/
├── frontend-bot/          ← Chat widget (HTML/CSS/JS)
│   ├── index.html
│   ├── style.css
│   └── script.js
├── data/                  ← Source documentation (.md file)
├── ingestion/              ← Scripts that chunk + embed + index the docs
├── retrieval/              ← Retrieval logic (Hugging Face embeddings)
├── generation/              ← Answer generation logic (Groq LLM)
├── vector_store/            ← MySQL chunk and embedding interface
├── tests/
├── api.py                  ← FastAPI app (all HTTP routes)
├── config.py                ← All settings (env vars, CORS, prefixes)
├── rag_pipeline.py           ← Orchestrates retrieval → generation → verification
├── requirements.txt
└── .env.example              ← Template for required secrets
```

---

## 1. Prerequisites

- **Python 3.10+** installed and added to PATH (`python --version` should work in your terminal)
- A **Hugging Face** account (free) → for embeddings
- A **Groq** account (free) → for answer generation
- A running **MySQL 8+** database and a database/user for this project

---

## 2. Install dependencies

From the project root (the folder containing `api.py`):

```bash
python -m pip install -r requirements.txt
python -m pip install sentence-transformers
```

> `sentence-transformers` isn't in `requirements.txt` but is required by the ingestion step — install it separately as shown above.

---

## 3. Set up environment variables

Copy the example env file:

```bash
copy .env.example .env        # Windows
cp .env.example .env           # Mac/Linux
```

Open `.env` and fill in:

```dotenv
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:5500
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=service_rag
MYSQL_PASSWORD=change-me
MYSQL_DATABASE=service_rag
```

**Where to get the keys:**
- **HF_TOKEN** → huggingface.co → Settings → Access Tokens → New token (Read access is enough)
- **GROQ_API_KEY** → console.groq.com → API Keys → Create API Key

`ALLOWED_ORIGINS` must include whatever address your frontend runs on. If you use VS Code's **Live Server** extension, that's usually `http://127.0.0.1:5500` — add your actual port if different.

### MySQL storage

MySQL is the only runtime database. It stores document metadata, document
versions, chunks, JSON chunk metadata, and 384-dimensional embeddings. Vector
retrieval applies the version filter in MySQL and calculates cosine similarity
with NumPy; SQLite, `sqlite-vec`, Qdrant, and a separate vector database are
not required.

For an existing `data/rag.db`, configure MySQL first and run the one-time
migration:

```bash
python scripts/migrate_sqlite_to_mysql.py
```

Use `SQLITE_SOURCE_PATH=/path/to/rag.db` when the legacy database is elsewhere.

---

## 4. Index the documentation

This step reads the `.md` file in `data/`, chunks it, generates embeddings, and stores them in MySQL. Run it once, and again any time the source document changes:

```bash
python -m ingestion.sync
```

You should see `RAG INDEX ACTIVATED` at the end with a chunk count. If it fails, check that MySQL is running and reachable, and that `HF_TOKEN` is set correctly.

---

## 5. Run the backend

```bash
python -m uvicorn api:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Verify it's working** — open in a browser:
- `http://127.0.0.1:8000/health` → should return `{"status":"ok",...}`
- `http://127.0.0.1:8000/ready` → should return `{"status":"ready","collection":"..."}`
  (If this returns `not_ready`, re-run step 4.)

Keep this terminal open — closing it stops the backend.

---

## 6. Run the frontend

The chat widget lives in `frontend-bot/index.html`. It's a plain HTML/CSS/JS app — no build step needed.

**Easiest way:** install the **Live Server** extension in VS Code, right-click `frontend-bot/index.html` → **"Open with Live Server."** It'll open in your browser, typically at `http://127.0.0.1:5500/frontend-bot/index.html`.

**First-time setup inside the widget:**
1. Click the chat bubble (bottom-right) to open it
2. Click the ⚙️ gear icon in the header
3. Set:
   - **API base URL:** `http://127.0.0.1:8000`
   - **Prefix:** `/api/v1` (must match `API_PREFIX` in `config.py`)
4. These are saved in your browser automatically — you won't need to re-enter them next time.

The status dot under "Chatbot" should turn **green ("Online")** once connected.

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Status dot shows "Offline" or HTTP error | Backend isn't running, or your frontend's address isn't in `ALLOWED_ORIGINS` in `.env` |
| Status dot shows "Index not ready" | Run `python -m ingestion.sync` (step 4) |
| Every question gets refused with "couldn't provide a reliable answer" | Check the backend terminal logs right after asking — look for `HF_TOKEN is not set` or Groq-related errors, meaning a key is missing/invalid; if keys are fine, the document may genuinely not cover that topic, or the question needs to be phrased closer to the doc's wording |
| `ModuleNotFoundError` on startup | Re-run step 2 (pip install) |
| `.env` changes don't seem to apply | Restart the backend — env vars are only read on startup, not on `--reload` |

---

## API Reference (for frontend/integration work)

**`POST /api/v1/chat`**
```json
// Request
{
  "version": 1,
  "query": "your question here",
  "url": "https://host-application.example/orders/123"
}

// Response
{
  "success": true,
  "answer": "...",
  "error": null,
  "request_id": "..."
}
```
`success: false` means the system deliberately declined to answer — this is expected behavior for a strict RAG system, not a bug. Sources, retrieved chunks, and internal scoring are never exposed by the API.

`version` is a global immutable document-set version. Every ready version contains one revision of every registered document. If any document changes, ingestion creates a new version while carrying unchanged document revisions forward. A request never searches across versions.

**`GET /api/v1/versions`** — lists ready global document-set versions available for chat.

To ingest a complete document set, provide its source directory explicitly:

```bash
python register_and_ingest_documents.py /path/to/current-document-set
```

Ingestion reuses unchanged document revisions and creates a new global version only when the complete revision mapping changes. It does not automatically choose that version for chat; the user selects a ready version from the frontend.

When the API is running, automatic ingestion watches source document-set directories matching `data/documents/version *`. After a debounced file add, edit, or delete, it runs the same complete-set ingestion flow in the background. It watches source sets only; generated paths such as `data/documents/1/versions/5` are not watched. Configure or disable this behavior with `RAG_AUTO_INGEST`, `RAG_INGEST_WATCH_ROOT`, `RAG_INGEST_SOURCE_SET_GLOB`, `RAG_INGEST_WATCH_INTERVAL_SECONDS`, and `RAG_INGEST_DEBOUNCE_SECONDS`.

### Performance configuration

The backend records stage timings for snapshot lookup, query rewriting, embedding, MySQL vector search, generation, claim validation, and verification. Performance options can be configured in `.env`:

```dotenv
RAG_TOP_K=3
RAG_MIN_SCORE=0.70
RAG_GENERATION_MAX_TOKENS=1000
RAG_VERIFIER_MAX_TOKENS=500
RAG_GENERATION_MODEL=openai/gpt-oss-20b
RAG_VERIFIER_MODEL=openai/gpt-oss-20b
RAG_REWRITE_MODEL=openai/gpt-oss-20b
RAG_ENABLE_QUERY_REWRITE=true
RAG_ENABLE_CACHE=true
RAG_CACHE_TTL_SECONDS=300
RAG_CACHE_MAX_ENTRIES=500
RAG_WARMUP_EMBEDDING_MODEL=true
```

Successful no-history answers are cached by `(global_version, normalized_query)`, so Version 1 and Version 2 can never share a cache entry. The embedding model and MySQL connection pool are reused within the backend process.

**`GET /health`** — liveness check.
**`GET /ready`** — confirms the vector index is active and populated.