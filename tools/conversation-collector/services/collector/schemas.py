"""Data schemas for the ConversationCollector service."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Types of messages in agent conversations."""
    AGENT_REQUEST = "agent_request"
    AGENT_RESPONSE = "agent_response"
    ORCHESTRATOR_ACTION = "orchestrator_action"
    WORKFLOW_START = "workflow_start"
    WORKFLOW_END = "workflow_end"


class ConversationMessage(BaseModel):
    """Structured representation of an agent conversation message."""
    id: str = Field(..., description="Unique message identifier")
    workflow_id: str = Field(..., description="Workflow instance identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_type: MessageType
    agent_name: Optional[str] = Field(None, description="Name of the agent (e.g., 'Frodo')")
    agent_role: Optional[str] = Field(None, description="Role of the agent (e.g., 'Hobbit')")
    orchestrator: Optional[str] = Field(None, description="Orchestrator name")
    content: str = Field(..., description="The actual message content")
    turn_number: Optional[int] = Field(None, description="Turn number in the conversation")
    topic: Optional[str] = Field(None, description="Pub/sub topic the message came from")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Original raw message data")


class ConversationSummary(BaseModel):
    """Summary of a conversation workflow."""
    workflow_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    orchestrator_type: Optional[str] = None
    agent_names: List[str] = Field(default_factory=list)
    message_count: int = 0
    status: str = "active"  # active, completed, failed


class GetConversationsRequest(BaseModel):
    """Request model for retrieving conversations."""
    workflow_id: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    message_type: Optional[MessageType] = None
    agent_name: Optional[str] = None


class GetConversationsResponse(BaseModel):
    """Response model for conversation retrieval."""
    messages: List[ConversationMessage]
    total_count: int
    has_more: bool