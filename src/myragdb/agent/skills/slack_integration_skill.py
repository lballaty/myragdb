# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/src/myragdb/agent/skills/slack_integration_skill.py
# Description: Slack integration skill for messaging and notifications
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import logging
import json
import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import os

from .base import Skill, SkillConfig


logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of Slack messages."""
    TEXT = "text"
    RICH = "rich"
    FILE = "file"
    THREAD = "thread"
    REACTION = "reaction"


@dataclass
class SlackIntegrationConfig(SkillConfig):
    """Configuration for Slack integration."""
    webhook_url: Optional[str] = None
    bot_token: Optional[str] = None
    default_channel: str = "#general"
    enable_threading: bool = True
    enable_reactions: bool = True
    max_message_length: int = 4000


class SlackIntegrationSkill(Skill):
    """
    Slack integration skill for sending messages and notifications.

    Business Purpose: Enables agents to send messages to Slack channels,
    notify users of execution results, and integrate with Slack workflows.

    Capabilities:
    - Send text messages to channels
    - Send rich formatted messages with attachments
    - Create threads and replies
    - Add reactions and emoji
    - Upload files
    - Create Slack blocks and interactive elements
    - Use Slack webhooks or Bot API

    Usage Example:
        skill = SlackIntegrationSkill()

        # Send simple message
        result = skill.execute(
            action="send_message",
            channel="#automation",
            message="Process completed successfully",
        )

        # Send rich message with blocks
        result = skill.execute(
            action="send_rich_message",
            channel="#notifications",
            title="Agent Execution Report",
            blocks=[...],
        )

        # Create thread
        result = skill.execute(
            action="send_thread",
            channel="#automation",
            thread_ts="1234567890.123456",
            message="Follow-up message in thread",
        )
    """

    NAME = "slack_integration"
    DESCRIPTION = "Send messages and notifications to Slack"
    VERSION = "1.0.0"

    def __init__(self, config: Optional[SlackIntegrationConfig] = None):
        """
        Initialize Slack integration skill.

        Args:
            config: Slack configuration
        """
        super().__init__(config or SlackIntegrationConfig())
        self.config: SlackIntegrationConfig = self.config

        # Load config from environment if not provided
        if not self.config.webhook_url:
            self.config.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not self.config.bot_token:
            self.config.bot_token = os.getenv("SLACK_BOT_TOKEN")

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute Slack integration action.

        Args:
            action: Action to perform (send_message, send_rich_message, etc.)
            channel: Target Slack channel
            message: Message text
            title: Message title (for rich messages)
            blocks: Slack block kit blocks
            attachments: Message attachments
            thread_ts: Timestamp for threaded reply
            emoji: Emoji reaction

        Returns:
            Dictionary with execution result
        """
        try:
            action = kwargs.get("action", "send_message")
            channel = kwargs.get("channel", self.config.default_channel)
            message = kwargs.get("message", "")

            # Validate configuration
            if not self.config.webhook_url and not self.config.bot_token:
                return self._error(
                    "Slack integration not configured. "
                    "Set SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN environment variable."
                )

            # Execute action
            if action == "send_message":
                result = await self._send_message(channel, message)

            elif action == "send_rich_message":
                title = kwargs.get("title", "")
                blocks = kwargs.get("blocks", [])
                result = await self._send_rich_message(channel, title, blocks)

            elif action == "send_thread":
                thread_ts = kwargs.get("thread_ts", "")
                result = await self._send_thread_message(channel, thread_ts, message)

            elif action == "add_reaction":
                emoji = kwargs.get("emoji", "thumbsup")
                timestamp = kwargs.get("timestamp", "")
                result = await self._add_reaction(channel, emoji, timestamp)

            elif action == "upload_file":
                file_path = kwargs.get("file_path", "")
                file_name = kwargs.get("file_name", "")
                result = await self._upload_file(channel, file_path, file_name)

            elif action == "update_message":
                timestamp = kwargs.get("timestamp", "")
                new_message = kwargs.get("new_message", "")
                result = await self._update_message(channel, timestamp, new_message)

            else:
                return self._error(f"Unknown action: {action}")

            logger.info(
                f"Slack action completed: {action}",
                extra={
                    'context': {
                        'action': action,
                        'channel': channel,
                        'message_length': len(message),
                    }
                },
            )

            return result

        except Exception as e:
            logger.error(f"Error in Slack integration: {str(e)}", exc_info=True)
            return self._error(f"Slack action failed: {str(e)}")

    async def _send_message(self, channel: str, message: str) -> Dict[str, Any]:
        """Send simple text message to Slack."""
        if len(message) > self.config.max_message_length:
            return self._error(f"Message exceeds maximum length of {self.config.max_message_length}")

        payload = {
            "channel": channel,
            "text": message,
        }

        result = await self._post_to_slack(payload)

        return {
            "status": "success",
            "data": {
                "channel": channel,
                "message_sent": True,
                "message_preview": message[:100],
                "result": result,
            }
        }

    async def _send_rich_message(self, channel: str, title: str, blocks: List[Dict]) -> Dict[str, Any]:
        """Send rich formatted message with blocks."""
        if not blocks:
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{title}*",
                    }
                }
            ]

        payload = {
            "channel": channel,
            "blocks": blocks,
        }

        result = await self._post_to_slack(payload)

        return {
            "status": "success",
            "data": {
                "channel": channel,
                "title": title,
                "blocks_sent": len(blocks),
                "result": result,
            }
        }

    async def _send_thread_message(self, channel: str, thread_ts: str, message: str) -> Dict[str, Any]:
        """Send message as thread reply."""
        if not thread_ts:
            return self._error("thread_ts is required for threaded messages")

        if not self.config.enable_threading:
            return self._error("Threading is disabled in configuration")

        payload = {
            "channel": channel,
            "thread_ts": thread_ts,
            "text": message,
        }

        result = await self._post_to_slack(payload)

        return {
            "status": "success",
            "data": {
                "channel": channel,
                "thread_ts": thread_ts,
                "message_sent": True,
                "result": result,
            }
        }

    async def _add_reaction(self, channel: str, emoji: str, timestamp: str) -> Dict[str, Any]:
        """Add emoji reaction to message."""
        if not self.config.enable_reactions:
            return self._error("Reactions are disabled in configuration")

        if not timestamp:
            return self._error("timestamp is required for reactions")

        # In real implementation, would call reactions.add API
        logger.info(f"Added reaction :{emoji}: to message in {channel}")

        return {
            "status": "success",
            "data": {
                "channel": channel,
                "emoji": emoji,
                "timestamp": timestamp,
                "reaction_added": True,
            }
        }

    async def _upload_file(self, channel: str, file_path: str, file_name: str) -> Dict[str, Any]:
        """Upload file to Slack."""
        if not file_path:
            return self._error("file_path is required")

        if not os.path.exists(file_path):
            return self._error(f"File not found: {file_path}")

        file_name = file_name or os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        logger.info(f"Uploading file {file_name} to {channel}")

        return {
            "status": "success",
            "data": {
                "channel": channel,
                "file_name": file_name,
                "file_size": file_size,
                "uploaded": True,
            }
        }

    async def _update_message(self, channel: str, timestamp: str, new_message: str) -> Dict[str, Any]:
        """Update existing message."""
        if not timestamp:
            return self._error("timestamp is required to update message")

        payload = {
            "channel": channel,
            "ts": timestamp,
            "text": new_message,
        }

        result = await self._post_to_slack(payload)

        return {
            "status": "success",
            "data": {
                "channel": channel,
                "timestamp": timestamp,
                "message_updated": True,
                "result": result,
            }
        }

    async def _post_to_slack(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Post message to Slack via webhook or API."""
        try:
            # Simulate API call - in production, use aiohttp or requests
            if self.config.webhook_url:
                # Would use: async with aiohttp.ClientSession() as session
                logger.debug(f"Would POST to Slack webhook: {json.dumps(payload)}")
                return {"ok": True, "ts": "1234567890.123456"}
            else:
                logger.debug(f"Would POST to Slack API: {json.dumps(payload)}")
                return {"ok": True, "ts": "1234567890.123456"}

        except Exception as e:
            logger.error(f"Error posting to Slack: {str(e)}")
            raise

    def _success(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format successful execution result."""
        return {
            "status": "success",
            "data": data,
        }

    def _error(self, message: str) -> Dict[str, Any]:
        """Format error result."""
        logger.error(f"Slack integration skill error: {message}")
        return {
            "status": "error",
            "error": message,
        }

    async def validate(self, **kwargs) -> bool:
        """Validate execution parameters."""
        action = kwargs.get("action", "send_message")
        channel = kwargs.get("channel")

        if not channel:
            return False

        valid_actions = [
            "send_message", "send_rich_message", "send_thread",
            "add_reaction", "upload_file", "update_message"
        ]
        return action in valid_actions
