"""
Smart City Assistant — SDG 11 (Sustainable Cities & Communities)
Next Gen Chatbot Arena submission.

Architecture (three boxes, same as the StudyBuddy pattern):
  UI (index.html)  -->  Backend (this file: /chat)  -->  LLM API (Gemini)

This file does two jobs at once, both required by the Arena rules:
  1. Serves the web chat UI at GET  /
  2. Exposes the graded API at      POST /chat   {"message": "..."} -> {"response": "..."}

Run locally:
  pip install -r requirements.txt
  uvicorn app:app --reload
  open http://localhost:8000
"""

import os
from typing import List, Literal

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

# ── 1. Setup ─────────────────────────────────────────────────────────────
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.5-flash-lite"
MAX_MESSAGE_CHARS = 2000
MAX_HISTORY_TURNS = 20  # keep the last N turns so requests don't grow unbounded

# Build the client once. If the key is missing we don't crash on import —
# we still want `GET /` to load and `/chat` to report a clear error,
# instead of the whole server refusing to start.
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

SYSTEM_PROMPT = """Role: You are UrbanEase, a friendly Smart City Assistant built for
SDG 11 — Sustainable Cities & Communities.

Task: Help everyday residents make their city more sustainable and liveable.
Cover sustainable transport, waste reduction and segregation, pollution
awareness, energy and water use around the home, public spaces, and civic
participation. Give practical, concrete help, not abstract theory.

Context: Users are residents of Indian towns and cities — students, families,
shopkeepers, commuters — asking everyday questions: cutting commute costs and
emissions, segregating waste properly, reporting a broken streetlight or
pothole, using less power or water at home, making a neighbourhood greener or
safer.

Rules:
- Use simple, clear English. Explain any technical term in a short phrase.
- Give 2-4 concrete steps the person can actually take, not vague advice.
- Never invent statistics, scheme names, or phone numbers. If you're not sure
  of a specific fact, say so plainly and point to the local municipal
  corporation website or official helpline instead of guessing.
- Do not give legal, medical, or emergency advice. For emergencies (fire,
  accident, crime), tell the user to contact local emergency services right
  away.
- Stay focused on sustainable-city topics. If asked something unrelated,
  gently acknowledge it, then steer back to how you can help with city and
  urban-living questions.
- Never suggest anything illegal, unsafe, or discriminatory.
- Keep replies under 150 words unless the user asks for more detail.
- End most replies with one short follow-up question or next step.
"""

app = FastAPI(title="Smart City Assistant API", version="1.0.0")

# The Arena evaluator calls this API from its own infrastructure, not a
# browser page on this domain — open CORS so that call is never blocked.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 2. Web UI ────────────────────────────────────────────────────────────
@app.get("/")
def home():
    return FileResponse("index.html", media_type="text/html")


@app.get("/health")
def health():
    return {"status": "ok", "gemini_key_configured": GEMINI_API_KEY is not None}


# ── 3. Chat API contract (POST /chat -> {"response": "..."}) ───────────────
class ChatTurn(BaseModel):
    role: Literal["user", "model"]
    text: str


class ChatRequest(BaseModel):
    message: str
    language: str = "English"
    history: list[ChatTurn] = []


def _error_body(text: str) -> dict:
    # Every response — success or failure — keeps the same {"response": "..."}
    # shape the Arena's evaluator expects, so a strict-JSON grader never
    # breaks even when something goes wrong upstream.
    return {"response": text, "error": True}


@app.post("/chat")
def chat(req: ChatRequest):
    message = req.message.strip() if req.message else ""

    if not message:
        return JSONResponse(status_code=400, content=_error_body(
            "Please send a non-empty 'message'."
        ))

    if len(message) > MAX_MESSAGE_CHARS:
        return JSONResponse(status_code=400, content=_error_body(
            f"That message is too long (limit {MAX_MESSAGE_CHARS} characters)."
        ))

    if client is None:
        return JSONResponse(status_code=500, content=_error_body(
            "The server is missing its GEMINI_API_KEY. Please contact the app admin."
        ))

    try:
        contents = [
            types.Content(role=turn.role, parts=[types.Part(text=turn.text)])
            for turn in req.history[-MAX_HISTORY_TURNS:]
            if turn.text.strip()
        ]
        contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

        result = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        )
        reply = (result.text or "").strip() or "I didn't catch that — could you rephrase?"
        return {"response": reply}

    except genai_errors.APIError as e:
        if e.code in (400, 401, 403):
            msg = "The chatbot's API key looks invalid or unauthorized. Please contact the app admin."
        elif e.code == 429:
            msg = "We're getting a lot of requests right now. Please wait a moment and try again."
        else:
            msg = "The chatbot service had a problem on its end. Please try again shortly."
        return JSONResponse(status_code=502, content=_error_body(msg))

    except Exception:
        return JSONResponse(status_code=500, content=_error_body(
            "Something went wrong answering that. Please try again."
        ))
