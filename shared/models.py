"""Pydantic models for FormalCC Runtime API."""

from typing import Optional, Any
from pydantic import BaseModel, Field


# Memory API Models
class MemoryPrefetchRequest(BaseModel):
    """Request for memory prefetch."""
    workspace_id: str
    session_id: str
    turn_id: str
    query: str
    limit: int = 10
    hints: Optional[dict[str, Any]] = None


class MemoryPrefetchResponse(BaseModel):
    """Response from memory prefetch."""
    memory_block: str
    retrieved_count: int = 0
    elapsed_ms: int = 0


class MemorySyncTurnRequest(BaseModel):
    """Request for syncing turn data."""
    workspace_id: str
    session_id: str
    turn_id: str
    user_message: str
    assistant_message: str
    metadata: Optional[dict[str, Any]] = None


class SessionEndRequest(BaseModel):
    """Request for ending a session."""
    workspace_id: str
    session_id: str
    metadata: Optional[dict[str, Any]] = None


# Compile API Models
class CompileRequest(BaseModel):
    """Request for context compilation."""
    scene: str = "auto"
    workspace_id: str
    session_id: str
    turn_id: str
    identity: Optional[dict[str, Any]] = None
    task: Optional[dict[str, Any]] = None
    hints: Optional[dict[str, Any]] = None


class CompiledMessage(BaseModel):
    """A compiled message."""
    role: str
    content: str


class Advisory(BaseModel):
    """Advisory information from compilation."""
    recommended_action: Optional[str] = None
    rationale_tail: Optional[str] = None


class CompileBundle(BaseModel):
    """Bundle returned from compilation."""
    scene: str
    compiled_messages: list[CompiledMessage] = Field(default_factory=list)
    evidence_units: list[dict[str, Any]] = Field(default_factory=list)
    supported_claims: list[dict[str, Any]] = Field(default_factory=list)
    advisory: Optional[Advisory] = None
    metrics: Optional[dict[str, Any]] = None


class CompileResponse(BaseModel):
    """Response from compile endpoint."""
    bundle: CompileBundle
