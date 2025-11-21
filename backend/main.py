from __future__ import annotations

import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

from schemas import AIRequest, AIResponse, ChatSession, Message, LearnifyInput, QuizRequest
from database import create_document, get_documents

app = FastAPI(title="ZoxNova API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EMERGENT_API_KEY = os.getenv("EMERGENT_API_KEY", "")
EMERGENT_MODEL = os.getenv("EMERGENT_MODEL", "gpt-5.1")

class ChatSaveRequest(BaseModel):
    title: str
    messages: List[Message]

@app.get("/test")
async def test():
    return {"status": "ok", "service": "ZoxNova API"}

@app.post("/ai", response_model=AIResponse)
async def ai_route(body: AIRequest):
    if not EMERGENT_API_KEY:
        # Fallback demo response for environments without key
        demo = "This is a demo response. Provide EMERGENT_API_KEY to enable real AI."
        return AIResponse(output=demo, meta={"model": EMERGENT_MODEL, "demo": True})

    try:
        # Single backend integration point
        payload: Dict[str, Any] = {
            "model": EMERGENT_MODEL,
            "messages": [m.model_dump() for m in (body.messages or [])] or (
                [{"role": "user", "content": body.prompt or ""}]
            ),
            "task": body.task,
        }
        headers = {
            "Authorization": f"Bearer {EMERGENT_API_KEY}",
            "Content-Type": "application/json",
        }
        # Hypothetical Emergent LLM endpoint
        resp = requests.post(
            "https://api.emergent-llm.com/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60,
        )
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        data = resp.json()
        output = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "No content returned")
        )
        meta = {"usage": data.get("usage", {}), "model": data.get("model", EMERGENT_MODEL)}
        return AIResponse(output=output, meta=meta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chats/save")
async def save_chat(body: ChatSaveRequest):
    created = await create_document("chat", body.model_dump())
    return {"ok": True, "chat": created}

@app.get("/chats")
async def list_chats(limit: int = 50):
    items = await get_documents("chat", {}, limit)
    return {"items": items}

@app.post("/learnify")
async def learnify_route(body: LearnifyInput):
    # Use AI route internally for transformations
    text = body.text or ""
    mode = body.mode.lower()
    prompt_map = {
        "explanation": f"Explain the following text simply and clearly:\n\n{text}",
        "flashcards": f"Create concise Q&A flashcards from this text:\n\n{text}\n\nReturn in JSON with fields: question, answer.",
        "summary": f"Summarize the following text into key bullet points:\n\n{text}",
        "mcqs": f"Generate 10 MCQs with options and correct answer from this text:\n\n{text}\nReturn JSON array with fields: question, options, correct",
    }
    prompt = prompt_map.get("explanation" if mode == "explanation" else mode, f"Process this text:\n{text}")
    ai_resp = await ai_route(AIRequest(task="summarize", prompt=prompt))
    return ai_resp

@app.post("/quizify")
async def quizify_route(body: QuizRequest):
    if body.mode.lower() == "daily":
        prompt = f"Create a daily 10-question quiz on the topic '{body.topic}'. Return JSON array with fields: question, options, correct."
    elif body.mode.lower() in ("stats", "ranks"):
        # Placeholder stats/ranks from DB later
        return {"mode": body.mode, "items": []}
    else:
        prompt = f"Generate {body.num_questions} MCQs about {body.topic}. Return JSON array with fields: question, options, correct."

    ai_resp = await ai_route(AIRequest(task="quiz", prompt=prompt))
    return ai_resp
