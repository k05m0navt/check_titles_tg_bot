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
            Telegram Bot API limitations:
            1. Username resolution requires chat_id context
            2. The user must be a member of the specified chat
            3. The user must have started/interacted with the bot
            4. For channels, bot must have admin privileges
        """
        try:
            # Remove @ if present and validate
            username = username.lstrip("@").strip()
            if not username:
                raise ValueError("Username cannot be empty")
            
            # Validate chat_id
            if not isinstance(chat_id, int) or chat_id == 0:
                raise ValueError(f"Invalid chat_id: must be a non-zero integer, got {type(chat_id).__name__}")
            
            # Try to get chat member - this requires:
            # 1. User must be a member of the chat
            # 2. User must have started/interacted with the bot (for private chats)
            # 3. Bot must have admin rights (for channels)
            try:
                # First, try with username as string (some bot API versions support this)
                chat_member = await self._bot.get_chat_member(chat_id, username)
            except (BadRequest, ValueError, TypeError) as e:
                # If username doesn't work, the error suggests the API might need user_id
                # This happens when username resolution isn't supported in this context
                error_msg = str(e).lower()
                if "invalid user" in error_msg or "user_id" in error_msg:
                    raise UserNotFoundError(
                        f"Cannot resolve username @{username} in chat {chat_id}. "
                        f"Possible reasons:\n"
                        f"• User @{username} is not a member of this chat\n"
                        f"• User hasn't started/interacted with the bot (required for username resolution)\n"
                        f"• Bot doesn't have admin rights in this chat/channel\n"
                        f"• Try adding the user to the chat first, or use the user's ID directly"
                    )
                # Re-raise other errors
                raise
            
            # Extract user_id from ChatMember object
            if chat_member and chat_member.user:
                return chat_member.user.id
            else:
                raise UserNotFoundError(f"User @{username} not found in chat {chat_id}")
                
        except BadRequest as e:
            error_msg = str(e).lower()
            # BadRequest usually means user not found or invalid chat_id
            if "user not found" in error_msg:
                raise UserNotFoundError(
                    f"User @{username} not found in chat {chat_id}. "
                    f"The user must be a member of this chat and have started the bot."
                )
            elif "chat not found" in error_msg or "chat_id" in error_msg:
                raise UserNotFoundError(f"Chat {chat_id} not found or bot is not a member")
            elif "invalid user" in error_msg or "user_id" in error_msg:
                raise UserNotFoundError(
                    f"Cannot resolve username @{username} in chat {chat_id}. "
                    f"The user must be a member of the chat and have started/interacted with the bot. "
                    f"Try: 1) Add the user to the chat, 2) Ask the user to start the bot, 3) Use user ID directly if available"
                )
            else:
                # Other BadRequest errors
                raise ValueError(f"Error resolving username @{username}: {str(e)}")
        except UserNotFoundError:
            # Re-raise UserNotFoundError as-is
            raise
        except TelegramError as e:
            # Network errors, rate limits, etc.
            raise ValueError(f"Telegram API error resolving username @{username}: {str(e)}")
        except Exception as e:
            # Unexpected errors
            raise ValueError(f"Unexpected error resolving username @{username}: {str(e)}")
