from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ConversationEntry(BaseModel):
    user_query: str
    bot_response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SessionData(BaseModel):
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: Optional[datetime] = None
    conversation_history: Optional[List[ConversationEntry]] = []
