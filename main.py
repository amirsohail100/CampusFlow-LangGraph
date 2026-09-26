import os
import uuid
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from agent import app as agent_app
from schema.payload import ChatRequest, ChatResponse, ProgrammeOption

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

app = FastAPI(title="College Assistant API", version="1.0.0")

# Rate limiting: IP address ke hisaab se limit lagayi hai taaki API / Agent calls abuse na hon.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Dev/Frontend CORS settings
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


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "College Assistant API"}


@app.get("/api/programmes")
def get_programmes():
    """List of programmes shown in the UI's dropdown."""
    return PROGRAMMES


# 10 requests per minute, per IP
@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
def chat(request: Request, payload: ChatRequest):
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
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    _sessions[session_id] = result

    reply = result["messages"][-1].content
    return ChatResponse(session_id=session_id, programme=payload.programme, reply=reply)


# Static assets mounting
if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# Frontend entry point (index.html)
@app.get("/")
def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Index file not found")