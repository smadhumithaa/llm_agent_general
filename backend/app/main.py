"""
FastAPI Application — LLM Agent
Routes:
  POST /ask             — run the agent
  POST /upload          — upload a file for summarization
  DELETE /session/{id}  — clear session memory
  GET  /tools           — list available tools
  GET  /health
"""
import os
import uuid
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from app.core.config import get_settings
from app.agent.react_agent import run_agent, clear_memory, ALL_TOOLS

settings = get_settings()

app = FastAPI(
    title="Aria — LLM Agent API",
    description="General-purpose ReAct agent powered by Gemini",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/tmp/agent_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Schemas ───────────────────────────────────────────────────────────────────
class AskRequest(BaseModel):
    question: str
    session_id: str = ""


class AgentStep(BaseModel):
    tool: str
    input: str
    observation: str


class AskResponse(BaseModel):
    answer: str
    steps: List[AgentStep]
    session_id: str
    tool_count: int


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "agent": "Aria", "model": settings.GEMINI_MODEL}


@app.get("/tools")
def list_tools():
    return {
        "tools": [
            {"name": t.name, "description": t.description[:120]}
            for t in ALL_TOOLS
        ]
    }


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """Run the ReAct agent on a question."""
    if not req.question.strip():
        raise HTTPException(400, "Question cannot be empty.")

    session_id = req.session_id or str(uuid.uuid4())

    try:
        result = run_agent(req.question, session_id)
    except Exception as e:
        err = str(e)
        lowered = err.lower()
        if (
            "resourceexhausted" in lowered
            or "quota exceeded" in lowered
            or "429" in lowered
        ):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini API quota exceeded for this key/project. "
                    "Enable billing or use a key/project with available quota, "
                    "then retry."
                ),
            )
        raise HTTPException(500, f"Agent error: {err}")

    return AskResponse(**result)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a PDF, DOCX, or TXT for the summarize_document tool."""
    allowed = {".pdf", ".docx", ".txt"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    dest = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"filename": file.filename, "status": "uploaded", "message": f"You can now ask me to summarize '{file.filename}'"}


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    clear_memory(session_id)
    return {"message": f"Session {session_id} cleared."}
