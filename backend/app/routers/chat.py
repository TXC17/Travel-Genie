"""
Conversational AI & Smart Replanning REST Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatSessionSchema,
    ChatSessionCreateRequest,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Conversational AI & Smart Replanning"])
service = ChatService()


@router.post("/sessions", response_model=ChatSessionSchema, status_code=status.HTTP_201_CREATED)
def create_chat_session(
    request: ChatSessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new conversational trip planning session for the authenticated user.
    """
    session = service.create_session(db, str(current_user.id), request)
    return session


@router.get("/sessions", response_model=List[ChatSessionSchema])
def list_user_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all chat sessions belonging to the authenticated user.
    """
    return service.get_user_sessions(db, str(current_user.id))


@router.get("/sessions/{session_id}", response_model=ChatSessionSchema)
def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch a specific chat session with its message history, enforcing ownership.
    """
    return service.get_session_by_id(db, session_id, str(current_user.id))


@router.post("/sessions/{session_id}/messages", response_model=SendMessageResponse)
def send_chat_message(
    session_id: str,
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a natural language travel prompt.
    Extracts structured constraints, executes the deterministic algorithm pipeline
    (MCDM -> K-Means -> OR-Tools), detects replanning diffs, persists the itinerary,
    and returns an explainable assistant response.
    """
    return service.process_message(db, session_id, str(current_user.id), request)
