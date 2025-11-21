from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Chat message schema
class Message(BaseModel):
    role: str = Field(..., description="user or assistant")
    content: str
    images: Optional[List[str]] = None

class ChatSession(BaseModel):
    title: str
    messages: List[Message]
    meta: Optional[Dict[str, Any]] = None

# Learnify schema
class LearnifyInput(BaseModel):
    text: Optional[str] = None
    file_url: Optional[str] = None
    mode: str = Field(..., description="explanation | flashcards | summary | mcqs")

# Quizify schema
class QuizRequest(BaseModel):
    topic: str
    mode: str = Field(..., description="daily | stats | ranks | custom")
    num_questions: int = 10

class AIRequest(BaseModel):
    task: str = Field(..., description="chat | summarize | essay | study_plan | explain_steps | quiz | diagram | pdf | images | videos")
    messages: Optional[List[Message]] = None
    prompt: Optional[str] = None

class AIResponse(BaseModel):
    output: str
    meta: Optional[Dict[str, Any]] = None
