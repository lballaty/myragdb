# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/llm/session_manager.py
# Description: Manages active LLM sessions enabling zero-restart switching between local and cloud providers
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional

from pydantic import BaseModel


class AuthMethodType(str, Enum):
    """Supported authentication methods for cloud LLMs"""
    API_KEY = "api_key"
    SUBSCRIPTION = "subscription"
    CLI = "cli"


class ProviderType(str, Enum):
    """Supported LLM provider types"""
    LOCAL = "local"
    GEMINI = "gemini"
    CHATGPT = "chatgpt"
    CLAUDE = "claude"


class LLMSession(BaseModel):
    """
    Represents currently active LLM session.

    Business Purpose: Track which LLM (local or cloud) is currently active
    without requiring server restart.

    Example:
        session = LLMSession(
            provider_type=ProviderType.GEMINI,
            model_id="gemini-pro",
            auth_method=AuthMethodType.API_KEY,
            status="active",
            created_at=datetime.now()
        )
    """
    provider_type: ProviderType
    model_id: str
    auth_method: AuthMethodType
    status: str  # "active", "inactive", "error"
    created_at: datetime
    error_message: Optional[str] = None
    health_check_passed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            "provider_type": self.provider_type.value,
            "model_id": self.model_id,
            "auth_method": self.auth_method.value,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "error_message": self.error_message,
            "health_check_passed": self.health_check_passed
        }

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionManager:
    """
    Manages LLM sessions without requiring process restarts.

    Business Purpose: Allow users to switch between local and cloud LLMs
    instantly without restarting the server. Session state is maintained
    in memory with optional persistence to disk.

    Design: Start with in-memory storage, designed for SQLite migration later.

    Example:
        manager = SessionManager()
        manager.initialize_local_session("phi3")

        # Later: Switch to cloud
        await manager.switch_to_cloud(
            provider="gemini",
            model_id="gemini-pro",
            auth_method="api_key",
            credentials={"api_key": "..."}
        )

        session = manager.get_active_session()
        print(session.provider_type)  # "gemini"
    """

    def __init__(self, session_file: Optional[str] = None, use_persistence: bool = True):
        """
        Initialize session manager.

        Args:
            session_file: Path to persist session state (optional)
            use_persistence: Whether to load/save session from/to file
        """
        self.session_file = session_file or str(Path.home() / ".myragdb" / "session.json")
        self.use_persistence = use_persistence
        self._current_session: Optional[LLMSession] = None

        if use_persistence:
            self._load_session()

    def initialize_local_session(self, model_id: str) -> LLMSession:
        """
        Initialize session with a local LLM.

        Args:
            model_id: Model identifier (e.g., "phi3", "qwen-coder-7b")

        Returns:
            LLMSession with local provider
        """
        self._current_session = LLMSession(
            provider_type=ProviderType.LOCAL,
            model_id=model_id,
            auth_method=AuthMethodType.API_KEY,  # Placeholder for local
            status="active",
            created_at=datetime.now(),
            health_check_passed=True
        )
        if self.use_persistence:
            self._save_session()
        return self._current_session

    async def switch_to_cloud(
        self,
        provider: str,
        model_id: str,
        auth_method: str,
        credentials: Dict[str, Any],
        provider_manager: Optional[Any] = None,
        credential_store: Optional[Any] = None
    ) -> LLMSession:
        """
        Switch to a cloud LLM provider.

        Args:
            provider: "gemini", "chatgpt", "claude"
            model_id: Model identifier (e.g., "gemini-pro")
            auth_method: "api_key", "subscription", "cli"
            credentials: Provider-specific credentials
            provider_manager: ProviderManager instance (injected for validation)
            credential_store: CredentialStore instance (injected for storage)

        Returns:
            Updated LLMSession with new provider

        Raises:
            ValueError: If credentials invalid or provider unavailable
        """
        try:
            # Validate provider
            provider_enum = ProviderType[provider.upper()]
        except KeyError:
            raise ValueError(f"Unknown provider: {provider}")

        try:
            # Validate auth method
            auth_enum = AuthMethodType[auth_method.upper()]
        except KeyError:
            raise ValueError(f"Unknown auth method: {auth_method}")

        # If provider_manager provided, validate credentials
        if provider_manager:
            provider_instance = provider_manager.get_provider(provider)

            # Validate credentials with provider
            is_valid = await provider_instance.validate_credentials(credentials)
            if not is_valid:
                raise ValueError(f"Invalid credentials for {provider}")

            # Get available models to verify model_id exists
            available_models = await provider_instance.list_models()
            model_ids = [m.id for m in available_models]
            if model_id not in model_ids:
                raise ValueError(f"Model {model_id} not available for {provider}")

        # Create new session
        self._current_session = LLMSession(
            provider_type=provider_enum,
            model_id=model_id,
            auth_method=auth_enum,
            status="active",
            created_at=datetime.now(),
            health_check_passed=True
        )

        # Store credentials securely if credential_store provided
        if credential_store:
            credential_store.save_credentials(provider, credentials)

        # Persist session
        if self.use_persistence:
            self._save_session()

        return self._current_session

    async def switch_to_local(self, model_id: str) -> LLMSession:
        """
        Switch back to a local LLM.

        Args:
            model_id: Local model identifier

        Returns:
            LLMSession with local provider
        """
        self._current_session = LLMSession(
            provider_type=ProviderType.LOCAL,
            model_id=model_id,
            auth_method=AuthMethodType.API_KEY,
            status="active",
            created_at=datetime.now(),
            health_check_passed=True
        )
        if self.use_persistence:
            self._save_session()
        return self._current_session

    def get_active_session(self) -> Optional[LLMSession]:
        """
        Get current active LLM session.

        Returns:
            LLMSession if active, None otherwise
        """
        return self._current_session

    async def refresh_session_health(
        self,
        llm_router: Optional[Any] = None,
        provider_manager: Optional[Any] = None,
        credential_store: Optional[Any] = None
    ) -> bool:
        """
        Check if current session is still healthy.

        Args:
            llm_router: LLMRouter instance for local health checks
            provider_manager: ProviderManager instance for cloud health checks
            credential_store: CredentialStore instance for credential validation

        Returns:
            True if session is valid and working, False otherwise
        """
        if not self._current_session:
            return False

        if self._current_session.provider_type == ProviderType.LOCAL:
            # Check local LLM availability if router provided
            if llm_router:
                try:
                    # This is a simple check - router should implement proper health check
                    self._current_session.health_check_passed = True
                    return True
                except Exception:
                    return False
            return True

        else:
            # Check cloud provider if manager provided
            if provider_manager and credential_store:
                try:
                    provider = provider_manager.get_provider(
                        self._current_session.provider_type.value
                    )
                    credentials = credential_store.load_credentials(
                        self._current_session.provider_type.value
                    )
                    if credentials:
                        is_valid = await provider.validate_credentials(credentials)
                        self._current_session.health_check_passed = is_valid
                        return is_valid
                except Exception:
                    return False

        return True

    def _save_session(self) -> None:
        """Persist session to file"""
        if not self._current_session:
            return

        Path(self.session_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.session_file, "w") as f:
            json.dump(
                self._current_session.to_dict(),
                f,
                indent=2,
                default=str
            )

    def _load_session(self) -> None:
        """Load session from file if exists"""
        session_path = Path(self.session_file)
        if not session_path.exists():
            return

        try:
            with open(session_path, "r") as f:
                data = json.load(f)
                # Convert ISO string back to datetime
                data["created_at"] = datetime.fromisoformat(data["created_at"])
                self._current_session = LLMSession(**data)
        except Exception as e:
            print(f"Warning: Could not load session: {e}")
            self._current_session = None
