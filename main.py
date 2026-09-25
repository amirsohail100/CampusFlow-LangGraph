"""
main.py
-------
FastAPI entrypoint for the College Assistant.

- Serves the chatbot UI (static/index.html, style.css, script.js)
- Exposes POST /api/chat which drives the LangGraph agent
- Keeps a simple in-memory conversation store keyed by session_id

Run with:
    uvicorn main:app --reload
"""

import os
import uuid
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from agent import app as agent_app
from schema.payload import ChatRequest, ChatResponse, ProgrammeOption

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

app = FastAPI(title="College Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# session_id -> {"programme": str, "messages": [...], "query_type": str, "retrieved_context": str}
_sessions: Dict[str, dict] = {}

PROGRAMMES = [
    ProgrammeOption(id="BCA", label="BCA"),
    ProgrammeOption(id="BBA", label="BBA"),
    ProgrammeOption(id="BCOM_H", label="B.Com (H)"),
]


@app.get("/api/programmes")
def get_programmes():
    """List of programmes shown in the UI's dropdown."""
    return PROGRAMMES


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = payload.session_id or str(uuid.uuid4())
    session_state = _sessions.get(session_id, {"messages": []})

    session_state["programme"] = payload.programme
    session_state["messages"] = list(session_state["messages"]) + [("human", payload.message)]

    try:
        result = agent_app.invoke(session_state)
    except FileNotFoundError as exc:
        # Raised by tools.nodes.build_retriever when a source PDF is missing.
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    _sessions[session_id] = result

    reply = result["messages"][-1].content
    return ChatResponse(session_id=session_id, programme=payload.programme, reply=reply)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
