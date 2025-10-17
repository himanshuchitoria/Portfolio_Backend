from pydantic import BaseModel, Field, constr
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class QueryRequest(BaseModel):
    """
    Request model for customer query submission.
    """
    query: constr(min_length=1) = Field(..., example="How do I reset my password?")
    session_id: Optional[UUID] = Field(None, description="Session ID to continue existing conversation")


class QueryResponse(BaseModel):
    """
    Response model for the AI-generated answer with session metadata.
    """
    response: str = Field(..., description="AI-generated response text")
    session_id: UUID = Field(..., description="Session identifier for conversation continuity")
    escalated: bool = Field(False, description="Flag indicating if escalation occurred")
    suggestions: Optional[List[str]] = Field(None, description="Suggested next actions after response")


class SessionInfo(BaseModel):
    """
    Model representing session summary information.
    """
    session_id: UUID = Field(..., description="Unique identifier for the session")
    query_history: List[str] = Field(default_factory=list, description="List of conversation queries and responses")
    created_at: datetime = Field(..., description="UTC timestamp when session was created")


class SummaryResponse(BaseModel):
    """
    Model for a conversation summary.
    """
    summary: str = Field(..., description="Concise summary of the conversation")




class MessageWithEmbedding(BaseModel):
    text: str
    embedding: Optional[List[float]] = None
    timestamp: datetime

class SessionInfo(BaseModel):
    session_id: UUID
    query_history: List[MessageWithEmbedding] = Field(default_factory=list)
    created_at: datetime
