# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/auth/flows/device_code_flow.py
# Description: Device code authentication flow for CLI users
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path
from uuid import uuid4
import time


@dataclass
class DeviceCode:
    """Represents a device code for CLI authentication"""
    device_code: str
    user_code: str
    provider: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_in: int = 900  # 15 minutes
    interval: int = 5  # Poll interval in seconds
    verification_url: str = ""
    status: str = "pending"  # pending, approved, denied, expired
    access_token: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'device_code': self.device_code,
            'user_code': self.user_code,
            'provider': self.provider,
            'created_at': self.created_at.isoformat(),
            'expires_in': self.expires_in,
            'interval': self.interval,
            'verification_url': self.verification_url,
            'status': self.status,
            'access_token': self.access_token,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DeviceCode':
        """Create from dictionary"""
        return cls(
            device_code=data['device_code'],
            user_code=data['user_code'],
            provider=data['provider'],
            created_at=datetime.fromisoformat(data['created_at']),
            expires_in=data.get('expires_in', 900),
            interval=data.get('interval', 5),
            verification_url=data.get('verification_url', ''),
            status=data.get('status', 'pending'),
            access_token=data.get('access_token'),
        )

    def is_expired(self) -> bool:
        """Check if device code has expired"""
        expiry = self.created_at + timedelta(seconds=self.expires_in)
        return datetime.now() > expiry


class DeviceCodeFlow:
    """
    Device code authentication flow for CLI users.

    Business Purpose: Enables CLI users to authenticate without exposing API keys
    in terminal history. Uses a simple user code shown in terminal, verification
    on a browser, then polls for approval.

    This flow is ideal for:
    - CLI tool authentication
    - CI/CD environments
    - Air-gapped systems
    - Automated scripts

    Usage Example:
        flow = DeviceCodeFlow()
        device_code = flow.initiate_device_flow('claude')
        print(f"Visit: {device_code.verification_url}")
        print(f"Enter code: {device_code.user_code}")

        token = flow.poll_for_approval(device_code.device_code)
        if token:
            flow.save_token(token)
    """

    # Device code endpoints per provider
    PROVIDER_ENDPOINTS = {
        'claude': {
            'device_code_url': 'https://auth.anthropic.com/device',
            'token_url': 'https://auth.anthropic.com/token',
        },
        'gpt': {
            'device_code_url': 'https://www.openai.com/auth/device',
            'token_url': 'https://www.openai.com/auth/token',
        },
        'gemini': {
            'device_code_url': 'https://accounts.google.com/o/device/code',
            'token_url': 'https://oauth2.googleapis.com/token',
        },
    }

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize Device Code Flow.

        Args:
            storage_dir: Directory to store device codes. Defaults to ~/.myragdb/device
        """
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path.home() / '.myragdb' / 'device'

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.codes_file = self.storage_dir / 'device_codes.json'

    def initiate_device_flow(self, provider: str) -> DeviceCode:
        """
        Initiate a device code authentication flow.

        Args:
            provider: Provider name (claude, gpt, gemini)

        Returns:
            DeviceCode instance with user_code and verification_url
        """
        if provider not in self.PROVIDER_ENDPOINTS:
            raise ValueError(f"Unknown provider: {provider}")

        # Generate codes
        device_code = uuid4().hex
        user_code = f"{uuid4().hex[:4]}-{uuid4().hex[:4]}".upper()

        device = DeviceCode(
            device_code=device_code,
            user_code=user_code,
            provider=provider,
            verification_url=f"https://{provider}.auth.myragdb.dev/device?code={user_code}",
            status="pending",
        )

        # Store device code
        self._store_device_code(device)

        return device

    def poll_for_approval(
        self,
        device_code: str,
        max_attempts: int = 180,  # 15 minutes with 5 second intervals
    ) -> Optional[str]:
        """
        Poll for user approval of device code.

        Args:
            device_code: Device code from initiate_device_flow
            max_attempts: Maximum number of poll attempts

        Returns:
            Access token if approved, None if denied or timed out
        """
        device = self._get_device_code(device_code)
        if not device:
            raise ValueError(f"Device code not found: {device_code}")

        if device.is_expired():
            device.status = "expired"
            self._store_device_code(device)
            return None

        attempts = 0
        while attempts < max_attempts:
            # Check approval status
            # In production, this would make an HTTP request to token_url
            if device.status == "approved":
                return device.access_token

            if device.status == "denied":
                return None

            if device.is_expired():
                device.status = "expired"
                self._store_device_code(device)
                return None

            # Wait and retry
            time.sleep(device.interval)
            attempts += 1

            # Reload device code to check for updates
            device = self._get_device_code(device_code)
            if not device:
                return None

        # Timeout
        device.status = "expired"
        self._store_device_code(device)
        return None

    def approve_device_code(self, user_code: str, access_token: str) -> bool:
        """
        Approve a device code (called by authorization server).

        Args:
            user_code: User code from device flow
            access_token: Access token to grant

        Returns:
            True if approval successful
        """
        codes = self._load_device_codes()
        for device_code_str, code_data in codes.items():
            if code_data['user_code'] == user_code:
                code_data['status'] = 'approved'
                code_data['access_token'] = access_token
                with open(self.codes_file, 'w') as f:
                    json.dump(codes, f, indent=2)
                return True
        return False

    def deny_device_code(self, user_code: str) -> bool:
        """
        Deny a device code (called by authorization server).

        Args:
            user_code: User code from device flow

        Returns:
            True if denial successful
        """
        codes = self._load_device_codes()
        for device_code_str, code_data in codes.items():
            if code_data['user_code'] == user_code:
                code_data['status'] = 'denied'
                with open(self.codes_file, 'w') as f:
                    json.dump(codes, f, indent=2)
                return True
        return False

    def list_pending_codes(self, provider: Optional[str] = None) -> list[DeviceCode]:
        """
        List pending device codes.

        Args:
            provider: Optional provider filter

        Returns:
            List of DeviceCode instances
        """
        codes = self._load_device_codes()
        result = []

        for code_data in codes.values():
            device = DeviceCode.from_dict(code_data)
            if device.status == "pending" and not device.is_expired():
                if provider is None or device.provider == provider:
                    result.append(device)

        return result

    def cleanup_expired_codes(self) -> int:
        """
        Remove expired device codes from storage.

        Returns:
            Number of codes removed
        """
        codes = self._load_device_codes()
        initial_count = len(codes)

        # Filter out expired codes
        codes = {
            k: v for k, v in codes.items()
            if not DeviceCode.from_dict(v).is_expired()
        }

        with open(self.codes_file, 'w') as f:
            json.dump(codes, f, indent=2)

        return initial_count - len(codes)

    def _store_device_code(self, device: DeviceCode) -> None:
        """Store device code to file"""
        codes = self._load_device_codes()
        codes[device.device_code] = device.to_dict()

        with open(self.codes_file, 'w') as f:
            json.dump(codes, f, indent=2)

    def _get_device_code(self, device_code: str) -> Optional[DeviceCode]:
        """Get device code from storage"""
        codes = self._load_device_codes()
        if device_code in codes:
            return DeviceCode.from_dict(codes[device_code])
        return None

    def _load_device_codes(self) -> dict:
        """Load device codes from storage"""
        if self.codes_file.exists():
            with open(self.codes_file, 'r') as f:
                return json.load(f)
        return {}
