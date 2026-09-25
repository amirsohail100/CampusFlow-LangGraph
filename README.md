# Campus Desk — College Assistant

A LangGraph-powered chatbot that answers student questions about academics
and fees, backed by two RAG pipelines over your college's own PDFs
(academics handbook + fee structure), served through a FastAPI backend
with a built-in web chat UI.

## Folder structure

```
college-assistant/
├── assets/
│   └── icon/
│       └── icon.svg          # app crest / favicon
├── data/
│   ├── academics_handbook.pdf   # add your own (see data/README.md)
│   └── fee_structure.pdf        # add your own (see data/README.md)
├── schema/
│   └── payload.py             # FastAPI request/response models
├── state/
│   └── StatePipeline.py       # shared LangGraph State TypedDict
├── tools/
│   └── nodes.py                # classifier, RAG, general & response nodes
├── static/
│   ├── index.html              # chatbot UI
│   ├── style.css
│   └── script.js
├── .env                        # GROQ_API_KEY goes here
├── .gitignore
├── agent.py                    # builds & compiles the LangGraph graph
├── main.py                     # FastAPI app (serves UI + /api/chat)
└── requirements.txt
```

## How it works

1. `classifier` node reads the latest message and labels it `academic`,
   `fee`, or `general`.
2. Depending on the label, the graph routes to `academic_rag` or `fee_rag`
   (FAISS + HuggingFace embeddings over your PDFs), or straight to
   `general` for small talk.
3. `response` node writes the final, programme-aware reply using Groq's
   `openai/gpt-oss-20b` model.
4. `main.py` exposes this graph as `POST /api/chat` and keeps a small
   in-memory conversation per `session_id`, and also serves the chat UI
   itself from `/static`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

1. Open `.env` and set your real `GROQ_API_KEY`.
2. Drop your two PDFs into `data/` (see `data/README.md` for exact names).
3. Run the server:

```bash
uvicorn main:app --reload
```

4. Open **http://localhost:8000** — the chat UI loads automatically.

## Notes / things you may want to change later

- Conversation state is kept in memory (a plain Python dict in `main.py`),
  so it resets if the server restarts. Swap in Redis or a database for
  production.
- FAISS indexes are rebuilt in memory on first use rather than persisted
  to disk — fine for small PDFs, worth caching for bigger ones.
- CORS is wide open (`allow_origins=["*"]`) for easy local testing —
  tighten this before deploying publicly.
