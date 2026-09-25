"""
payload.py
----------
Pydantic models describing the shape of data going in and out of the
FastAPI endpoints.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(default="", description="Client-generated session id. Leave empty to start a new session.")
    programme: str = Field(..., description="Student's programme, e.g. BCA, BBA or BCOM_H")
    message: str = Field(..., min_length=1, description="The student's question")


class ChatResponse(BaseModel):
    session_id: str
    programme: str
    reply: str


class ProgrammeOption(BaseModel):
    id: str
    label: str
