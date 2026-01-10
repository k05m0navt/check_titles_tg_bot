"""Telegram user resolver service for resolving usernames to user IDs."""

from typing import Optional
from telegram import Bot
from telegram.error import TelegramError, BadRequest

from ...domain.exceptions import UserNotFoundError


class TelegramUserResolver:
    """Service for resolving Telegram usernames to user IDs via Bot API."""

    def __init__(self, bot_instance: Bot):
        """Initialize resolver with bot instance.
        
        Args:
            bot_instance: Telegram Bot instance for API calls
        """
        self._bot = bot_instance

    async def resolve_username_to_user_id(self, username: str, chat_id: int) -> int:
        """Resolve username to Telegram user ID using Bot API.
        
        Args:
            username: Telegram username (without @)
            chat_id: Chat ID where username should be resolved (required by Telegram API)
            
        Returns:
            Telegram user ID (int)
            
        Raises:
            UserNotFoundError: If username doesn't exist in chat or cannot be resolved
            ValueError: If network/API error occurs (not user not found)
            
        Note:
            Telegram Bot API limitation: Username resolution requires chat_id context.
            Cannot resolve username to user_id without chat context.
        """
        try:
            # Remove @ if present
            username = username.lstrip("@")
            
            # Get chat member to resolve username to user_id
            chat_member = await self._bot.get_chat_member(chat_id, username)
            
            # Extract user_id from ChatMember object
            if chat_member and chat_member.user:
                return chat_member.user.id
            else:
                raise UserNotFoundError(f"User @{username} not found in chat {chat_id}")
                
        except BadRequest as e:
            # BadRequest usually means user not found or invalid chat_id
            if "user not found" in str(e).lower() or "chat not found" in str(e).lower():
                raise UserNotFoundError(f"User @{username} not found in Telegram chat {chat_id}")
            else:
                # Other BadRequest errors (invalid parameters, etc.)
                raise ValueError(f"Error resolving username @{username}: {str(e)}")
        except TelegramError as e:
            # Network errors, rate limits, etc.
            raise ValueError(f"Telegram API error resolving username @{username}: {str(e)}")
        except Exception as e:
            # Unexpected errors
            raise ValueError(f"Unexpected error resolving username @{username}: {str(e)}")
