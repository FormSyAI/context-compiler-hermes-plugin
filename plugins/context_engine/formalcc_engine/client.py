"""Client wrapper for context engine."""

import logging
from typing import Optional, Any

from shared import RuntimeClient
from shared.models import CompileRequest, CompileBundle
from shared.errors import RuntimeAPIError, TimeoutError as FormalCCTimeoutError

logger = logging.getLogger("formalcc.engine.client")


class EngineClient:
    """Client for context engine Runtime API calls."""

    def __init__(self, runtime_client: RuntimeClient):
        self.runtime_client = runtime_client

    async def compile(
        self,
        workspace_id: str,
        session_id: str,
        turn_id: str,
        scene: str = "auto",
        identity: Optional[dict[str, Any]] = None,
        task: Optional[dict[str, Any]] = None,
        hints: Optional[dict[str, Any]] = None,
    ) -> Optional[CompileBundle]:
        """Compile context via Runtime API."""
        try:
            request = CompileRequest(
                scene=scene,
                workspace_id=workspace_id,
                session_id=session_id,
                turn_id=turn_id,
                identity=identity,
                task=task,
                hints=hints,
            )

            response = await self.runtime_client.compile(request)
            logger.info(
                f"Compile completed: scene={response.bundle.scene}, "
                f"elapsed={response.bundle.metrics.get('elapsed_ms', 'N/A')}ms"
            )
            return response.bundle

        except (RuntimeAPIError, FormalCCTimeoutError) as e:
            logger.warning(f"Compile failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in compile: {e}")
            return None
