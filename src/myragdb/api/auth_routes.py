# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/api/auth_routes.py
# Description: FastAPI routes for authentication management
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from myragdb.auth import AuthenticationManager, UserCredential, AuthMethod

# Initialize router and auth manager
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
auth_manager = AuthenticationManager()


# ==================== Request/Response Models ====================

class APIKeyCredentialRequest(BaseModel):
    """Request to create API key credential"""
    provider: str = Field(..., description="LLM provider (claude, gpt, gemini)")
    api_key: str = Field(..., description="API key from provider")
    description: Optional[str] = Field(None, description="Optional description")
    set_as_default: bool = Field(True, description="Set as default for provider")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "claude",
                "api_key": "sk-ant-...",
                "description": "Production API key",
                "set_as_default": True
            }
        }


class OAuthInitiateResponse(BaseModel):
    """Response with OAuth authorization URL"""
    provider: str
    authorization_url: str
    description: str = "Visit this URL in your browser to authorize"


class OAuthCompleteRequest(BaseModel):
    """Request to complete OAuth authentication"""
    provider: str = Field(..., description="Provider name")
    auth_code: str = Field(..., description="Authorization code from provider")
    state: Optional[str] = Field(None, description="State parameter for CSRF protection")
    set_as_default: bool = Field(True, description="Set as default for provider")


class DeviceCodeInitiateResponse(BaseModel):
    """Response with device code for CLI auth"""
    device_code: str
    user_code: str
    provider: str
    verification_url: str
    expires_in: int
    interval: int
    instructions: str = "Visit the verification URL and enter the user code"


class DeviceCodeCompleteRequest(BaseModel):
    """Request to complete device code authentication"""
    device_code: str = Field(..., description="Device code from initiation")
    set_as_default: bool = Field(True, description="Set as default for provider")


class CredentialResponse(BaseModel):
    """Credential information response"""
    credential_id: str
    provider: str
    auth_method: str
    identifier: str
    is_active: bool
    is_default: bool


class CredentialListResponse(BaseModel):
    """List of credentials"""
    total: int
    credentials: List[CredentialResponse]
    providers: List[str] = Field(description="Unique providers in list")


# ==================== API Key Endpoints ====================

@router.post("/credentials/api-key")
async def create_api_key_credential(
    request: APIKeyCredentialRequest
) -> CredentialResponse:
    """
    Create a new API key credential.

    Business Purpose: Allow users to directly provide API keys for LLM providers.
    Suitable for production, CI/CD, and programmatic access.

    Request:
        provider: LLM provider name (claude, gpt, gemini)
        api_key: The actual API key from provider
        description: Optional human-readable description
        set_as_default: Whether to use as default for provider

    Response:
        credential_id: Unique credential identifier
        provider: Provider name
        auth_method: "api_key"
        identifier: API key ID
        is_active: Whether credential is active
        is_default: Whether default for provider
    """
    credential = auth_manager.authenticate_with_api_key(
        provider=request.provider,
        api_key=request.api_key,
        description=request.description or "",
        set_as_default=request.set_as_default,
    )

    if not credential:
        raise HTTPException(status_code=400, detail="Failed to create API key credential")

    return CredentialResponse(
        credential_id=credential.credential_id,
        provider=credential.provider,
        auth_method=credential.auth_method.value,
        identifier=credential.identifier,
        is_active=credential.is_active,
        is_default=credential.is_default,
    )


@router.get("/credentials/api-key")
async def list_api_key_credentials(
    provider: Optional[str] = Query(None, description="Filter by provider")
) -> CredentialListResponse:
    """
    List all API key credentials.

    Query Parameters:
        provider: Optional provider name to filter by

    Response:
        total: Number of credentials
        credentials: List of credential details
        providers: Unique providers in list
    """
    credentials = auth_manager.list_api_key_credentials(provider)
    providers = list(set(c.provider for c in credentials))

    return CredentialListResponse(
        total=len(credentials),
        credentials=[
            CredentialResponse(
                credential_id=c.credential_id,
                provider=c.provider,
                auth_method=c.auth_method.value,
                identifier=c.identifier,
                is_active=c.is_active,
                is_default=c.is_default,
            )
            for c in credentials
        ],
        providers=providers,
    )


# ==================== OAuth Endpoints ====================

@router.post("/oauth/initiate")
async def initiate_oauth(
    provider: str = Query(..., description="Provider name (claude, gpt, gemini)")
) -> OAuthInitiateResponse:
    """
    Initiate OAuth authentication flow.

    Business Purpose: Start web-based OAuth flow for secure provider authorization.
    User visits returned URL, consents, and is redirected with authorization code.

    Query Parameters:
        provider: LLM provider name

    Response:
        provider: Provider name
        authorization_url: URL for user to visit
        description: Instructions for user
    """
    auth_url = auth_manager.initiate_oauth(provider)

    if not auth_url:
        raise HTTPException(status_code=400, detail=f"Failed to initiate OAuth for {provider}")

    return OAuthInitiateResponse(
        provider=provider,
        authorization_url=auth_url,
    )


@router.post("/oauth/complete")
async def complete_oauth(request: OAuthCompleteRequest) -> CredentialResponse:
    """
    Complete OAuth authentication with authorization code.

    Business Purpose: Exchange authorization code for access token and save credential.

    Request:
        provider: Provider name
        auth_code: Authorization code from provider
        state: CSRF protection state parameter
        set_as_default: Whether to use as default

    Response:
        Credential details
    """
    credential = auth_manager.complete_oauth(
        provider=request.provider,
        auth_code=request.auth_code,
        state=request.state,
        set_as_default=request.set_as_default,
    )

    if not credential:
        raise HTTPException(status_code=400, detail="Failed to complete OAuth authentication")

    return CredentialResponse(
        credential_id=credential.credential_id,
        provider=credential.provider,
        auth_method=credential.auth_method.value,
        identifier=credential.identifier,
        is_active=credential.is_active,
        is_default=credential.is_default,
    )


@router.get("/oauth/credentials")
async def list_oauth_credentials(
    provider: Optional[str] = Query(None, description="Filter by provider")
) -> CredentialListResponse:
    """
    List all OAuth credentials.

    Query Parameters:
        provider: Optional provider name to filter by

    Response:
        List of OAuth credentials
    """
    credentials = auth_manager.list_oauth_credentials(provider)
    providers = list(set(c.provider for c in credentials))

    return CredentialListResponse(
        total=len(credentials),
        credentials=[
            CredentialResponse(
                credential_id=c.credential_id,
                provider=c.provider,
                auth_method=c.auth_method.value,
                identifier=c.identifier,
                is_active=c.is_active,
                is_default=c.is_default,
            )
            for c in credentials
        ],
        providers=providers,
    )


# ==================== Device Code Endpoints ====================

@router.post("/device-code/initiate")
async def initiate_device_code(
    provider: str = Query(..., description="Provider name")
) -> DeviceCodeInitiateResponse:
    """
    Initiate device code authentication for CLI users.

    Business Purpose: Enable CLI authentication without exposing keys in terminal.
    User visits verification URL with user code, approves, then CLI polls for token.

    Query Parameters:
        provider: LLM provider name

    Response:
        device_code: Code to track device flow
        user_code: Short code for user to enter
        verification_url: URL for user to visit
        expires_in: Expiration time in seconds
        interval: Poll interval in seconds
    """
    device_code = auth_manager.initiate_device_code(provider)

    if not device_code:
        raise HTTPException(status_code=400, detail=f"Failed to initiate device code for {provider}")

    return DeviceCodeInitiateResponse(
        device_code=device_code.device_code,
        user_code=device_code.user_code,
        provider=device_code.provider,
        verification_url=device_code.verification_url,
        expires_in=device_code.expires_in,
        interval=device_code.interval,
    )


@router.post("/device-code/complete")
async def complete_device_code(
    request: DeviceCodeCompleteRequest
) -> CredentialResponse:
    """
    Complete device code authentication by polling for approval.

    Business Purpose: Poll for user approval of device code authorization.

    Request:
        device_code: Device code from initiation
        set_as_default: Whether to use as default

    Response:
        Credential details if approved
    """
    credential = auth_manager.complete_device_code(
        device_code=request.device_code,
        set_as_default=request.set_as_default,
    )

    if not credential:
        raise HTTPException(status_code=400, detail="Device code not approved or expired")

    return CredentialResponse(
        credential_id=credential.credential_id,
        provider=credential.provider,
        auth_method=credential.auth_method.value,
        identifier=credential.identifier,
        is_active=credential.is_active,
        is_default=credential.is_default,
    )


@router.get("/device-code/credentials")
async def list_device_code_credentials(
    provider: Optional[str] = Query(None, description="Filter by provider")
) -> CredentialListResponse:
    """
    List all device code credentials.

    Query Parameters:
        provider: Optional provider name to filter by

    Response:
        List of device code credentials
    """
    credentials = auth_manager.list_device_code_credentials(provider)
    providers = list(set(c.provider for c in credentials))

    return CredentialListResponse(
        total=len(credentials),
        credentials=[
            CredentialResponse(
                credential_id=c.credential_id,
                provider=c.provider,
                auth_method=c.auth_method.value,
                identifier=c.identifier,
                is_active=c.is_active,
                is_default=c.is_default,
            )
            for c in credentials
        ],
        providers=providers,
    )


# ==================== Credential Management Endpoints ====================

@router.get("/credentials")
async def list_all_credentials(
    provider: Optional[str] = Query(None, description="Filter by provider")
) -> CredentialListResponse:
    """
    List all credentials across all auth methods.

    Query Parameters:
        provider: Optional provider name to filter by

    Response:
        List of all credentials
    """
    credentials = auth_manager.list_credentials(provider)
    providers = list(set(c.provider for c in credentials))

    return CredentialListResponse(
        total=len(credentials),
        credentials=[
            CredentialResponse(
                credential_id=c.credential_id,
                provider=c.provider,
                auth_method=c.auth_method.value,
                identifier=c.identifier,
                is_active=c.is_active,
                is_default=c.is_default,
            )
            for c in credentials
        ],
        providers=providers,
    )


@router.get("/credentials/default/{provider}")
async def get_default_credential(provider: str) -> CredentialResponse:
    """
    Get default credential for a provider.

    Path Parameters:
        provider: Provider name

    Response:
        Default credential for provider, or 404 if none exists
    """
    credential = auth_manager.get_credential(provider)

    if not credential:
        raise HTTPException(status_code=404, detail=f"No default credential for {provider}")

    return CredentialResponse(
        credential_id=credential.credential_id,
        provider=credential.provider,
        auth_method=credential.auth_method.value,
        identifier=credential.identifier,
        is_active=credential.is_active,
        is_default=credential.is_default,
    )


@router.patch("/credentials/{credential_id}/default")
async def set_default_credential(credential_id: str) -> dict:
    """
    Set a credential as default for its provider.

    Path Parameters:
        credential_id: Credential ID to set as default

    Response:
        Success message
    """
    if not auth_manager.set_default_credential(credential_id):
        raise HTTPException(status_code=404, detail="Credential not found")

    return {"status": "success", "message": "Credential set as default"}


@router.delete("/credentials/{credential_id}")
async def delete_credential(credential_id: str) -> dict:
    """
    Delete a credential completely.

    Path Parameters:
        credential_id: Credential ID to delete

    Response:
        Success message
    """
    if not auth_manager.delete_credential(credential_id):
        raise HTTPException(status_code=404, detail="Credential not found")

    return {"status": "success", "message": "Credential deleted"}


@router.post("/credentials/{credential_id}/revoke")
async def revoke_credential(credential_id: str) -> dict:
    """
    Revoke a credential (deactivate without deletion).

    Path Parameters:
        credential_id: Credential ID to revoke

    Response:
        Success message
    """
    if not auth_manager.revoke_credential(credential_id):
        raise HTTPException(status_code=404, detail="Credential not found")

    return {"status": "success", "message": "Credential revoked"}
