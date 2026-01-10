"""Chat member handler for bot-added-to-group events."""

from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
import structlog

from ...domain.repositories.user_repository import IUserRepository
from ..utils.localization import get_user_language
from ...infrastructure.i18n.translations import translate

logger = structlog.get_logger(__name__)


class ChatMemberHandler:
    """Handler for processing bot-added-to-group events."""

    def __init__(self, user_repository: IUserRepository):
        """
        Initialize chat member handler.
        
        Args:
            user_repository: User repository interface (for language detection)
        """
        self._user_repository = user_repository

    async def handle_new_chat_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle NEW_CHAT_MEMBERS status update - detect when bot is added to group."""
        message = update.message
        if not message or not message.new_chat_members:
            return

        # Check if bot itself is in new_chat_members list
        bot_id = context.bot.id if context.bot else None
        if not bot_id:
            logger.warning("Cannot determine bot ID, skipping new_chat_members handler")
            return

        # Check if bot was added to the group
        bot_was_added = any(member.id == bot_id for member in message.new_chat_members)
        
        if not bot_was_added:
            # Bot was not added, skip
            return

        # Bot was added to group - send welcome message
        chat = message.chat
        if not chat:
            logger.warning("Cannot determine chat for new_chat_members handler")
            return

        # Determine language (default to English for group messages)
        # Try to get language from message sender if available, otherwise default to English
        sender_language = "en"
        if message.from_user:
            try:
                sender_user = await self._user_repository.get_by_telegram_id(message.from_user.id)
                if sender_user:
                    sender_language = sender_user.language
            except Exception:
                # If error getting user language, use default
                pass

        # Build welcome message
        welcome_text = "👋 Welcome! To use this bot, please run /register to register yourself.\n\n"
        welcome_text += "Available commands:\n"
        welcome_text += "• /register - Register yourself with the bot\n"
        welcome_text += "• /me - View your stats\n"
        welcome_text += "• /who @username - View another user's stats\n"
        welcome_text += "• /leaderboard - View leaderboard\n"
        welcome_text += "• /stats - View statistics\n"
        welcome_text += "• /help - Show help message"

        try:
            # Send welcome message to the group
            await message.reply_text(welcome_text)
            logger.info(
                "Welcome message sent after bot was added to group",
                chat_id=chat.id,
                chat_type=chat.type
            )
        except Exception as e:
            logger.error(
                "Error sending welcome message after bot was added to group",
                error=str(e),
                chat_id=chat.id,
                chat_type=chat.type,
                exc_info=True
            )
