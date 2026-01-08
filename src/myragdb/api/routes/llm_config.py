# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/api/routes/llm_config.py
# Description: API endpoints for persistent LLM provider configuration across browsers
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-08

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel
from myragdb.db.llm_config import LLMProviderConfigDatabase

router = APIRouter(prefix="/api/v1", tags=["llm-config"])

# Initialize database handler
llm_config_db = LLMProviderConfigDatabase()


class SetProviderRequest(BaseModel):
    """Request to set current LLM provider."""
    provider_name: str
    auth_method: Optional[str] = None


class ProviderConfigUpdate(BaseModel):
    """Request to update provider configuration."""
    provider_name: str
    display_name: str
    auth_method: Optional[str] = None
    enabled: bool = True


class ProviderConfigResponse(BaseModel):
    """Response with current provider configuration."""
    provider_name: Optional[str]
    auth_method: Optional[str]


@router.get("/llm-config/provider")
async def get_current_provider() -> Dict[str, Optional[str]]:
    """
    Get the currently selected LLM provider.

    Business Purpose: Returns the user's globally selected cloud LLM provider
    and authentication method (persisted across all browsers).

    Returns:
        Dictionary with provider_name and auth_method (both None if using local LLM)

    Example:
        GET /api/v1/llm-config/provider
        Response: {
            "provider_name": "claude",
            "auth_method": "api_key"
        }
    """
    try:
        result = llm_config_db.get_current_provider()

        if result:
            provider_name, auth_method = result
            return {"provider_name": provider_name, "auth_method": auth_method}
        else:
            return {"provider_name": None, "auth_method": None}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm-config/provider")
async def set_current_provider(request: SetProviderRequest) -> Dict[str, str]:
    """
    Set the currently selected LLM provider globally.

    Business Purpose: Persists user's provider selection across all browser instances
    and server restarts, ensuring consistent experience across devices.

    Args:
        provider_name: Provider identifier (e.g., 'claude', 'chatgpt', 'gemini')
        auth_method: Authentication method ('api_key', 'oauth', 'device_code')

    Returns:
        Success message

    Example:
        POST /api/v1/llm-config/provider
        Body: {
            "provider_name": "claude",
            "auth_method": "api_key"
        }
        Response: {"status": "success", "message": "Provider updated"}
    """
    try:
        success = llm_config_db.set_current_provider(
            request.provider_name,
            request.auth_method
        )

        if success:
            return {
                "status": "success",
                "message": f"Provider set to {request.provider_name}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update provider")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/llm-config/provider")
async def clear_current_provider() -> Dict[str, str]:
    """
    Clear the current LLM provider (revert to local LLM).

    Business Purpose: Allows user to switch back to local LLM across all instances.

    Returns:
        Success message

    Example:
        DELETE /api/v1/llm-config/provider
        Response: {"status": "success", "message": "Provider cleared"}
    """
    try:
        success = llm_config_db.clear_current_provider()

        if success:
            return {
                "status": "success",
                "message": "Provider cleared, using local LLM"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear provider")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm-config/provider/{provider_name}")
async def get_provider_config(provider_name: str) -> Dict[str, Any]:
    """
    Get configuration details for a specific provider.

    Args:
        provider_name: Provider identifier

    Returns:
        Provider configuration details or not found error

    Example:
        GET /api/v1/llm-config/provider/claude
        Response: {
            "provider_name": "claude",
            "display_name": "Claude (Anthropic)",
            "enabled": true,
            "auth_method": "api_key",
            "configured_at": 1704733200,
            "last_used_at": 1704733245
        }
    """
    try:
        config = llm_config_db.get_provider_config(provider_name)

        if config:
            return config
        else:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not configured")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/llm-config/provider/{provider_name}")
async def update_provider_config(
    provider_name: str,
    request: ProviderConfigUpdate
) -> Dict[str, str]:
    """
    Update configuration for a provider.

    Args:
        provider_name: Provider identifier
        display_name: User-friendly name
        auth_method: Authentication method used
        enabled: Whether provider is active

    Returns:
        Success message

    Example:
        PUT /api/v1/llm-config/provider/claude
        Body: {
            "provider_name": "claude",
            "display_name": "Claude (Anthropic)",
            "auth_method": "api_key",
            "enabled": true
        }
        Response: {"status": "success", "message": "Provider configured"}
    """
    try:
        success = llm_config_db.update_provider_config(
            provider_name,
            request.display_name,
            request.auth_method,
            request.enabled
        )

        if success:
            return {
                "status": "success",
                "message": f"Provider {provider_name} configured"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update provider")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
