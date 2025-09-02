"""
Avatar integration models for LiveKit Agents.
Follows SOLID principles with abstract interfaces and concrete implementations.
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any

from livekit.agents import AgentSession
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AvatarProviderType(Enum):
    """Enumeration of supported avatar providers."""
    BEYOND_PRESENCE = "bey"
    ANAM = "anam"
    BITHUMAN = "bithuman"
    HEDRA = "hedra"
    SIMLI = "simli"
    TAVUS = "tavus"


class AvatarConfig(BaseModel):
    """Base configuration for avatar sessions."""
    provider: AvatarProviderType
    avatar_participant_identity: Optional[str] = None
    avatar_participant_name: Optional[str] = None
    enabled: bool = True

    # Provider-specific configurations
    bey_avatar_id: Optional[str] = None
    anam_avatar_id: Optional[str] = None
    anam_name: Optional[str] = None
    bithuman_model_path: Optional[str] = None
    hedra_avatar_id: Optional[str] = None
    simli_face_id: Optional[str] = None
    tavus_avatar_id: Optional[str] = None


class AvatarProvider(ABC):
    """Abstract base class for avatar providers following the Strategy pattern."""

    def __init__(self, config: AvatarConfig):
        self.config = config
        self._session: Optional[Any] = None

    @abstractmethod
    async def create_session(self) -> Any:
        """Create the avatar session instance."""
        pass

    @abstractmethod
    async def start(self, agent_session: AgentSession, livekit_url: str, room: Any) -> bool:
        """Start the avatar session and return success status."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the avatar session."""
        pass

    @property
    def is_active(self) -> bool:
        """Check if the avatar session is active."""
        return self._session is not None


class BeyondPresenceAvatarProvider(AvatarProvider):
    """Beyond Presence avatar provider implementation."""

    async def create_session(self) -> Any:
        try:
            from livekit.plugins import bey

            avatar_id = self.config.bey_avatar_id
            if not avatar_id:
                logger.error("Beyond Presence avatar requires bey_avatar_id")
                return None
            identity = self.config.avatar_participant_identity or "bey-avatar-agent"
            name = self.config.avatar_participant_name or "bey-avatar-agent"

            return bey.AvatarSession(
                avatar_id=avatar_id,
                avatar_participant_identity=identity,
                avatar_participant_name=name
            )
        except ImportError as e:
            logger.error(f"Failed to import Beyond Presence plugin: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create Beyond Presence avatar session: {e}")
            return None

    async def start(self, agent_session: AgentSession, livekit_url: str, room: Any) -> bool:
        try:
            self._session = await self.create_session()
            if self._session is None:
                return False

            await self._session.start(agent_session, livekit_url=livekit_url, room=room)
            logger.info("Beyond Presence avatar started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start Beyond Presence avatar: {e}")
            return False

    async def stop(self) -> None:
        if self._session:
            try:
                # Beyond Presence doesn't have a stop method, just clear reference
                self._session = None
                logger.info("Beyond Presence avatar stopped")
            except Exception as e:
                logger.error(f"Error stopping Beyond Presence avatar: {e}")


class AnamAvatarProvider(AvatarProvider):
    """Anam avatar provider implementation."""

    async def create_session(self) -> Any:
        try:
            from livekit.plugins import anam

            avatar_id = self.config.anam_avatar_id
            name = self.config.anam_name

            if not avatar_id or not name:
                logger.error("Anam avatar requires both avatar_id and name")
                return None

            return anam.AvatarSession(
                persona_config=anam.PersonaConfig(
                    name=name,
                    avatar_id=avatar_id
                ),
                avatar_participant_name=self.config.avatar_participant_name or "anam-avatar-agent"
            )
        except ImportError as e:
            logger.error(f"Failed to import Anam plugin: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create Anam avatar session: {e}")
            return None

    async def start(self, agent_session: AgentSession, livekit_url: str, room: Any) -> bool:
        try:
            self._session = await self.create_session()
            if self._session is None:
                return False

            await self._session.start(agent_session, livekit_url=livekit_url, room=room)
            logger.info("Anam avatar started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start Anam avatar: {e}")
            return False

    async def stop(self) -> None:
        if self._session:
            try:
                # Anam doesn't have a stop method, just clear reference
                self._session = None
                logger.info("Anam avatar stopped")
            except Exception as e:
                logger.error(f"Error stopping Anam avatar: {e}")


class BitHumanAvatarProvider(AvatarProvider):
    """BitHuman avatar provider implementation."""

    async def create_session(self) -> Any:
        try:
            from livekit.plugins import bithuman

            model_path = self.config.bithuman_model_path
            if not model_path:
                logger.error("BitHuman avatar requires model_path")
                return None

            return bithuman.AvatarSession(
                model_path=model_path
            )
        except ImportError as e:
            logger.error(f"Failed to import BitHuman plugin: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create BitHuman avatar session: {e}")
            return None

    async def start(self, agent_session: AgentSession, livekit_url: str, room: Any) -> bool:
        try:
            self._session = await self.create_session()
            if self._session is None:
                return False

            await self._session.start(agent_session, livekit_url=livekit_url, room=room)
            logger.info("BitHuman avatar started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start BitHuman avatar: {e}")
            return False

    async def stop(self) -> None:
        if self._session:
            try:
                # BitHuman doesn't have a stop method, just clear reference
                self._session = None
                logger.info("BitHuman avatar stopped")
            except Exception as e:
                logger.error(f"Error stopping BitHuman avatar: {e}")


class AvatarSession:
    """Main avatar session manager that handles multiple avatar providers."""

    def __init__(self, config: AvatarConfig):
        self.config = config
        self.providers: Dict[AvatarProviderType, AvatarProvider] = {}
        self._active_provider: Optional[AvatarProvider] = None

        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize avatar providers based on configuration."""
        if self.config.provider == AvatarProviderType.BEYOND_PRESENCE:
            self.providers[AvatarProviderType.BEYOND_PRESENCE] = BeyondPresenceAvatarProvider(self.config)
        elif self.config.provider == AvatarProviderType.ANAM:
            self.providers[AvatarProviderType.ANAM] = AnamAvatarProvider(self.config)
        elif self.config.provider == AvatarProviderType.BITHUMAN:
            self.providers[AvatarProviderType.BITHUMAN] = BitHumanAvatarProvider(self.config)
        # Add other providers as needed

    async def start(self, agent_session: AgentSession, livekit_url: str, room: Any) -> bool:
        """Start the avatar session with error handling."""
        if not self.config.enabled:
            logger.info("Avatar is disabled, skipping avatar start")
            return True

        provider_type = self.config.provider
        if provider_type not in self.providers:
            logger.error(f"Avatar provider {provider_type} not supported")
            return False

        try:
            provider = self.providers[provider_type]
            success = await provider.start(agent_session, livekit_url, room)

            if success:
                self._active_provider = provider
                logger.info(f"Avatar {provider_type.value} started successfully")
            else:
                logger.warning(f"Failed to start avatar {provider_type.value}, continuing without avatar")

            return True  # Always return True to not crash the session

        except Exception as e:
            logger.error(f"Unexpected error starting avatar {provider_type.value}: {e}")
            logger.info("Continuing without avatar to maintain session stability")
            return True  # Return True to not crash the session

    async def stop(self) -> None:
        """Stop the active avatar session."""
        if self._active_provider:
            await self._active_provider.stop()
            self._active_provider = None

    @property
    def is_active(self) -> bool:
        """Check if any avatar is currently active."""
        return self._active_provider is not None and self._active_provider.is_active


class AvatarFactory:
    """Factory class for creating avatar configurations following the Factory pattern."""

    @staticmethod
    def create_beyond_presence_config(
            avatar_id: str,
            participant_identity: Optional[str] = None,
            participant_name: Optional[str] = None,
            enabled: bool = True
    ) -> AvatarConfig:
        """Create Beyond Presence avatar configuration."""
        return AvatarConfig(
            provider=AvatarProviderType.BEYOND_PRESENCE,
            bey_avatar_id=avatar_id,
            avatar_participant_identity=participant_identity,
            avatar_participant_name=participant_name,
            enabled=enabled
        )

    @staticmethod
    def create_anam_config(
            avatar_id: str,
            name: str,
            participant_name: Optional[str] = None,
            enabled: bool = True
    ) -> AvatarConfig:
        """Create Anam avatar configuration."""
        return AvatarConfig(
            provider=AvatarProviderType.ANAM,
            anam_avatar_id=avatar_id,
            anam_name=name,
            avatar_participant_name=participant_name,
            enabled=enabled
        )

    @staticmethod
    def create_bithuman_config(
            model_path: str,
            enabled: bool = True
    ) -> AvatarConfig:
        """Create BitHuman avatar configuration."""
        return AvatarConfig(
            provider=AvatarProviderType.BITHUMAN,
            bithuman_model_path=model_path,
            enabled=enabled
        )
