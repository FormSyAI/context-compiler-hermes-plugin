"""Client wrapper for memory provider."""

import logging
from typing import Optional, Any

from shared import RuntimeClient
from shared.models import (
    MemoryPrefetchRequest,
    MemoryPrefetchResponse,
    MemorySyncTurnRequest,
    SessionEndRequest,
)
from shared.errors import RuntimeAPIError, TimeoutError as FormalCCTimeoutError

logger = logging.getLogger("formalcc.memory.client")


class MemoryClient:
    """Client for memory-related Runtime API calls."""

    def __init__(self, runtime_client: RuntimeClient):
        self.runtime_client = runtime_client

    async def prefetch(
        self,
        workspace_id: str,
        session_id: str,
        turn_id: str,
        query: str,
        hints: Optional[dict[str, Any]] = None,
    ) -> str:
        """Prefetch memory and return memory block."""
        try:
            request = MemoryPrefetchRequest(
                workspace_id=workspace_id,
                session_id=session_id,
                turn_id=turn_id,
                query=query,
                limit=10,
                hints=hints,
            )

            response = await self.runtime_client.memory_prefetch(request)
            logger.info(f"Memory prefetch completed: {response.elapsed_ms}ms")
            return response.memory_block

        except (RuntimeAPIError, FormalCCTimeoutError) as e:
            logger.warning(f"Prefetch failed: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error in prefetch: {e}")
            return ""

    async def sync_turn(
        self,
        workspace_id: str,
        session_id: str,
        turn_id: str,
        user_message: str,
        assistant_message: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Sync turn data (non-blocking)."""
        try:
            request = MemorySyncTurnRequest(
                workspace_id=workspace_id,
                session_id=session_id,
                turn_id=turn_id,
                user_message=user_message,
                assistant_message=assistant_message,
                metadata=metadata,
            )

            await self.runtime_client.memory_sync_turn(request)
            logger.info(f"Memory sync completed: turn={turn_id}")

        except Exception as e:
            logger.error(f"Sync turn failed: {e}")
