from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import asyncio

from app.config import settings
from app.services.session_manager import session_manager
from app.services.llm_integration import LLMClient
from app.services.faq_handler import FAQHandler
from app.services.escalation_handler import EscalationHandler
from app.api.models import QueryRequest, QueryResponse, SessionInfo, SummaryResponse

router = APIRouter()

# Dependency providers
def get_session_manager():
    return session_manager

def get_llm_client():
    return LLMClient(api_key=settings.gemini_api_key)

def get_faq_handler():
    return FAQHandler()

def get_escalation_handler():
    return EscalationHandler()

def convert_history_to_messages(history_strings: List[str]) -> List[dict]:
    return [
        {
            "text": text,
            "embedding": None,
            "timestamp": datetime.utcnow(),
        }
        for text in history_strings
    ]

# defined api endpoints here
@router.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
async def handle_query(
    request: QueryRequest,
    session_manager=Depends(get_session_manager),
    llm_client: LLMClient = Depends(get_llm_client),
    faq_handler: FAQHandler = Depends(get_faq_handler),
    escalation_handler: EscalationHandler = Depends(get_escalation_handler),
):
    session_id_str: Optional[str] = str(request.session_id) if request.session_id else None

    if session_id_str:
        session = await session_manager.get_session(session_id_str)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found.")
    else:
        session = await session_manager.create_session()

    # for faq check
    faq_answer = faq_handler.get_faq_answer(request.query)

    if faq_answer:
        response_text = faq_answer
        escalated = False
    else:
        # contextual memory
        conversation_history = await session_manager.get_conversation_history(session.session_id)

        contextual_memory = []
        if hasattr(session_manager, "get_contextual_memory"):
            contextual_memory = await session_manager.get_contextual_memory(session.session_id)

        full_context = contextual_memory + conversation_history

        # llm response with full context
        llm_result = await llm_client.generate_response(request.query, full_context)

        response_text = llm_result.get("text", "")
        escalated = llm_result.get("escalated", False)

        # If escalated, generate detailed escalation note
        if escalated:
            escalation_note = escalation_handler.create_escalation_note(request.query, conversation_history)
            response_text = escalation_note
            # Optionally notify support team asynchronously
            asyncio.create_task(escalation_handler.notify_support_team(escalation_note))

    # Add query/response to session
    await session_manager.add_to_conversation(session.session_id, request.query, response_text)

    # Obtain suggested next actions
    

    return QueryResponse(
        response=response_text,
        session_id=session.session_id,
        escalated=escalated,
        
    )



@router.get("/session/{session_id}/", response_model=SessionInfo)
async def get_session(
    session_id: UUID,
    session_manager=Depends(get_session_manager),
):
    session = await session_manager.get_session(str(session_id))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    return SessionInfo(
        session_id=session.session_id,
        query_history=convert_history_to_messages(session.query_history),
        created_at=session.created_at,
    )

@router.get("/sessions", response_model=List[SessionInfo])
async def list_sessions(session_manager=Depends(get_session_manager)):
    sessions = await session_manager.list_sessions()
    return [
        SessionInfo(
            session_id=s.session_id,
            query_history=convert_history_to_messages(s.query_history),
            created_at=s.created_at,
        )
        for s in sessions
    ]

@router.post("/summarize/{session_id}", response_model=SummaryResponse)
async def summarize_session(
    session_id: UUID,
    llm_client: LLMClient = Depends(get_llm_client),
    session_manager=Depends(get_session_manager),
):
    summary_text = await llm_client.summarize_session(str(session_id))
    if hasattr(session_manager, "store_session_summary"):
        await session_manager.store_session_summary(str(session_id), summary_text)
    return SummaryResponse(summary=summary_text)



@router.post("/session/create", status_code=status.HTTP_201_CREATED)
async def create_session_with_greeting(
    session_manager=Depends(get_session_manager),
):
    session = await session_manager.create_session()

    bot_greeting = "Hello! How can I assist you today? (This model is still under development, so please excuse any limitations. If found some bug, please escalate the issue by simply asking to escalate.)"

    await session_manager.add_to_conversation(session.session_id, user_query="", bot_response=bot_greeting)

    return {
        "session_id": session.session_id,
        "bot_message": bot_greeting,
        "escalated": False
       
    }
