"""FormalCC Context Engine implementation."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from shared import RuntimeClient
from shared.errors import RuntimeAPIError
from .config import EngineConfigManager, EngineConfig
from .client import EngineClient
from .message_converter import (
    convert_compile_bundle_to_messages,
    detect_scene,
    extract_task,
)

logger = logging.getLogger("formalcc.engine")


class ContextEngine(ABC):
    """Abstract base class for Hermes context engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Engine name."""
        pass

    @abstractmethod
    async def update_from_response(self, response: dict, context: dict) -> None:
        """Update internal state from model response."""
        pass

    @abstractmethod
    def should_compress(
        self, messages: list[dict], token_count: int, threshold: int
    ) -> bool:
        """Determine if compression should occur."""
        pass

    @abstractmethod
    async def compress(
        self,
        messages: list[dict],
        context: dict,
        focus_topic: Optional[str] = None,
    ) -> list[dict]:
        """Compress/compile context and return OpenAI-style messages."""
        pass


class FormalCCContextEngine(ContextEngine):
    """FormalCC Context Engine for Hermes."""

    def __init__(self):
        self._config: Optional[EngineConfig] = None
        self._runtime_client: Optional[RuntimeClient] = None
        self._engine_client: Optional[EngineClient] = None
        self._session_id: Optional[str] = None
        self._turn_counter: int = 0

    @property
    def name(self) -> str:
        return "formalcc-engine"

    async def initialize(self, config: dict, hermes_home: Path) -> None:
        """Initialize context engine."""
        logger.info("Initializing formalcc-engine context engine")

        config_manager = EngineConfigManager(hermes_home)
        self._config = config_manager.load_config(config)

        self._runtime_client = RuntimeClient(
            base_url=self._config.base_url,
            api_key_env=self._config.api_key_env,
            timeout_s=self._config.timeout_s,
            max_retries=self._config.max_retries,
        )

        await self._runtime_client.__aenter__()
        self._engine_client = EngineClient(self._runtime_client)

        logger.info("Engine initialized successfully")

    async def update_from_response(self, response: dict, context: dict) -> None:
        """Update internal state from model response."""
        self._turn_counter += 1
        if "session_id" in context:
            self._session_id = context["session_id"]

    def should_compress(
        self, messages: list[dict], token_count: int, threshold: int
    ) -> bool:
        """Returns True when token count exceeds threshold."""
        return token_count > threshold

    async def compress(
        self,
        messages: list[dict],
        context: dict,
        focus_topic: Optional[str] = None,
    ) -> list[dict]:
        """Compile context via FormalCC Runtime."""
        if not self._engine_client:
            logger.warning("Engine client not initialized; returning original messages")
            return messages

        session_id = context.get("session_id", "unknown")
        self._session_id = session_id
        turn_id = f"{session_id}_turn_{self._turn_counter:04d}"

        # Detect scene from context
        scene = detect_scene(context)

        # Build identity hints
        identity: Optional[dict] = None
        if repo_id := context.get("repo_id"):
            identity = {
                "repo_id": repo_id,
                "revision": context.get("revision", "main"),
            }
        elif document_id := context.get("document_id"):
            identity = {"document_id": document_id}

        # Extract task from messages
        task = extract_task(messages)

        # Build hints
        hints: dict = {}
        if focus_topic:
            hints["focus_topic"] = focus_topic
        hints["bypass_router"] = False

        logger.info(
            f"Compiling context: session={session_id}, scene={scene}, "
            f"focus_topic={focus_topic}"
        )

        bundle = await self._engine_client.compile(
            workspace_id=self._config.workspace_id,
            session_id=session_id,
            turn_id=turn_id,
            scene=scene,
            identity=identity,
            task=task,
            hints=hints,
        )

        if bundle is None:
            # Graceful degradation: return original messages
            logger.warning("Compile failed; returning original messages")
            return messages

        compiled = convert_compile_bundle_to_messages(bundle)

        if not compiled:
            logger.warning("Compile returned empty messages; returning originals")
            return messages

        logger.info(f"Compiled to {len(compiled)} messages (was {len(messages)})")
        return compiled
