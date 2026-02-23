"""
Tool 5 — Document Summarizer
Accepts a file path (PDF or DOCX) already uploaded by the user.
Extracts text and summarizes using Gemini.
"""
import os
from pathlib import Path
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

from app.core.config import get_settings

settings = get_settings()

UPLOAD_DIR = "/tmp/agent_uploads"


def _extract_text(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    elif ext == ".docx":
        import docx
        doc = docx.Document(file_path)
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}")


@tool
def summarize_document(filename: str) -> str:
    """
    Summarize a document that the user has uploaded.
    Input: the filename (e.g. "report.pdf" or "notes.docx").
    Returns a concise structured summary with key points.
    """
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        available = os.listdir(UPLOAD_DIR) if os.path.exists(UPLOAD_DIR) else []
        return (
            f"File '{filename}' not found in uploads.\n"
            f"Available files: {available or 'none uploaded yet'}"
        )

    try:
        text = _extract_text(file_path)
    except Exception as e:
        return f"Could not read file: {e}"

    if not text.strip():
        return "The document appears to be empty or unreadable."

    # Truncate to ~12k chars to stay within context limits
    truncated = text[:12000]
    if len(text) > 12000:
        truncated += "\n\n[Document truncated — showing first 12,000 characters]"

    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
        max_retries=settings.GEMINI_MAX_RETRIES,
    )

    prompt = f"""Summarize the following document. Structure your response as:

**Overview** (2-3 sentences)

**Key Points**
- Point 1
- Point 2
- ...

**Notable Details** (any important numbers, dates, names)

Document:
{truncated}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content
