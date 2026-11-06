# company-policy-assistant
An internal policy assistant that answers employee questions from company policy documents using RAG with Qdrant. It gives cited answers and says when a policy doesn't cover the question.

## How it works

**Upload** (`POST /api/documents`): save the PDF to `data/` → read text page by page → split into chunks → embed with Azure OpenAI → store in Qdrant.

**Ask** (`POST /api/ask`): embed the question → find the closest chunks in Qdrant → Claude answers from those chunks with `[1]`-style citations. If no chunk scores above `MIN_SCORE`, the answer is "not covered" and Claude isn't called.

## Project structure

```
app/
├── main.py                # entry point: creates the FastAPI app
├── core/
│   ├── config.py          # settings, loaded from .env
│   ├── exceptions.py      # app errors and their HTTP status codes
│   └── logging.py
├── api/
│   ├── dependencies.py    # builds the Azure, Qdrant and Claude clients once
│   ├── router.py          # api_router: every endpoint's URL prefix and tag
│   └── endpoints/         # documents.py, ask.py, health.py
├── schemas/               # request and response models
└── services/
    ├── pdf_loader.py      # PDF → pages
    ├── chunker.py         # pages → chunks
    ├── embeddings.py      # text → vectors (Azure OpenAI)
    ├── vector_store.py    # store, search, delete (Qdrant)
    ├── llm.py             # answer with citations (Claude via Azure AI Foundry)
    ├── document_store.py  # uploaded PDFs on disk
    ├── ingestion.py       # upload pipeline
    └── qa.py              # question pipeline
```

## Setup

1. Create `.env` in the project root with the settings listed in `app/core/config.py`.
2. Install:
   ```
   pip install -r requirements.txt
   ```

## Run

From the project root:
```
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs to upload PDFs and ask questions.
