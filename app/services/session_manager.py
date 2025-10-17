import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

from app.database.mongodb import sessions_collection, conversations_collection
from app.config import settings

class Session:
    """
    Represents a customer support conversation session.
    """
    def __init__(self, session_id: str, created_at: datetime, query_history: Optional[List[str]] = None):
        self.session_id = session_id
        self.created_at = created_at
        self.query_history = query_history or []

class SessionManager:
    """
    Manages sessions and conversation context for the AI Customer Support bot.
    Maintains in-memory cache and persists data to MongoDB.
    """

    def __init__(self):
        # In-memory cache for sessions - session_id -> Session
        self._sessions: Dict[str, Session] = {}
        # Lock for async-safe session cache modifications
        self._lock = asyncio.Lock()
        # Session expiration timedelta; comment out filtering to debug
        # self._expiration_delta = timedelta(minutes=settings.session_expiration_minutes)
        # For debugging, disable expiration filtering to always fetch all sessions
        self._expiration_delta = timedelta(days=365*10)  # 10 years, effectively disables expiration

    async def get_contextual_memory(self, session_id: str) -> List[str]:
        memories_docs = await sessions_collection.find_one({"_id": session_id})
        if not memories_docs or "contextual_memory" not in memories_docs:
            return []
        return memories_docs.get("contextual_memory", [])

    async def store_contextual_memory(self, session_id: str, memory_items: List[str]) -> None:
        await sessions_collection.update_one(
            {"_id": session_id},
            {"$set": {"contextual_memory": memory_items}},
            upsert=True
        )

    async def store_session_summary(self, session_id: str, summary_text: str) -> None:
        existing_memory = await self.get_contextual_memory(session_id)
        updated_memory = existing_memory + [f"Summary: {summary_text}"]
        await self.store_contextual_memory(session_id, updated_memory)

    async def create_session(self) -> Session:
        async with self._lock:
            session_id = str(uuid4())
            now = datetime.utcnow()
            session = Session(session_id=session_id, created_at=now)
            self._sessions[session_id] = session

            session_doc = {
                "_id": session_id,
                "created_at": now,
                "last_active_at": now,
                "conversation_history": [],
            }
            await sessions_collection.insert_one(session_doc)

            return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                if datetime.utcnow() - session.created_at > self._expiration_delta:
                    await self.delete_session(session_id)
                    return None
                return session

        session_doc = await sessions_collection.find_one({"_id": session_id})
        if not session_doc:
            return None

        conversation_docs = await conversations_collection.find(
            {"session_id": session_id}
        ).sort("timestamp").to_list(length=None)

        history = []
        for entry in conversation_docs:
            if "user_query" in entry:
                history.append(entry["user_query"])
            if "bot_response" in entry:
                history.append(entry["bot_response"])

        loaded_session = Session(
            session_id=session_doc["_id"],
            created_at=session_doc["created_at"],
            query_history=history,
        )

        async with self._lock:
            self._sessions[session_id] = loaded_session

        return loaded_session

    async def add_to_conversation(self, session_id: str, user_query: str, bot_response: str) -> None:
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                session = await self.get_session(session_id)
                if not session:
                    raise ValueError("Session not found")

            session.query_history.append(user_query)
            session.query_history.append(bot_response)

        conversation_doc = {
            "session_id": session_id,
            "user_query": user_query,
            "bot_response": bot_response,
            "timestamp": datetime.utcnow(),
        }
        await conversations_collection.insert_one(conversation_doc)

        await sessions_collection.update_one(
            {"_id": session_id},
            {"$set": {"last_active_at": datetime.utcnow()}},
        )

    async def get_conversation_history(self, session_id: str) -> List[str]:
        async with self._lock:
            session = self._sessions.get(session_id)
        if session:
            return session.query_history

        conversation_docs = await conversations_collection.find(
            {"session_id": session_id}
        ).sort("timestamp").to_list(length=None)

        history = []
        for entry in conversation_docs:
            if "user_query" in entry:
                history.append(entry["user_query"])
            if "bot_response" in entry:
                history.append(entry["bot_response"])
        return history

    async def list_sessions(self) -> List[Session]:
        async with self._lock:
            cached_sessions = list(self._sessions.values())

        expiration_threshold = datetime.utcnow() - self._expiration_delta
        cursor = sessions_collection.find({"last_active_at": {"$gte": expiration_threshold}})
        db_sessions_docs = await cursor.to_list(length=None)

        db_sessions = []
        for doc in db_sessions_docs:
            db_sessions.append(Session(session_id=doc["_id"], created_at=doc["created_at"], query_history=[]))

        all_sessions_dict = {s.session_id: s for s in cached_sessions}
        for s in db_sessions:
            if s.session_id not in all_sessions_dict:
                all_sessions_dict[s.session_id] = s

        return list(all_sessions_dict.values())

    async def delete_session(self, session_id: str) -> None:
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]

        await sessions_collection.delete_one({"_id": session_id})
        await conversations_collection.delete_many({"session_id": session_id})


# Singleton session manager instance
session_manager = SessionManager()
