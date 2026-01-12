"""Message handler for monitoring @HowGayBot messages."""

from datetime import date
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
import structlog

from ...domain.repositories.user_repository import IUserRepository
from ...domain.value_objects.percentage import Percentage
from ...application.services.message_parser import MessageParser
from ...application.use_cases.update_title_use_case import UpdateTitleUseCase
from ...domain.exceptions import TitleLockedError, InvalidPercentageError, UserNotFoundError
from ..utils.localization import get_user_language
from ...infrastructure.i18n.translations import translate

logger = structlog.get_logger(__name__)


class MessageHandler:
    """Handler for processing messages from @HowGayBot."""

    def __init__(
        self,
        user_repository: IUserRepository,
        update_title_use_case: UpdateTitleUseCase,
    ):
        """
        Initialize message handler.
        
        Args:
            user_repository: User repository interface
            update_title_use_case: Update title use case
        """
        self._user_repository = user_repository
        self._update_title_use_case = update_title_use_case

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming message - filter for @HowGayBot messages."""
        message = update.message
        if not message:
            return

        # Check if message is from or via @HowGayBot
        if not MessageParser.should_process_message(message):
            return

        # Extract percentage
        try:
            percentage = MessageParser.extract_percentage(message.text or "")
        except InvalidPercentageError as e:
            logger.warning(
                "Invalid percentage in @HowGayBot message",
                message_text=message.text,
                error=str(e)
            )
            return

        # Identify target user
        target_user = await self._identify_target_user(message)
        if not target_user:
            logger.warning(
                "Cannot identify target user for @HowGayBot message",
                message_text=message.text,
                reply_to_message_id=message.reply_to_message.message_id if message.reply_to_message else None,
                via_bot=message.via_bot.username if message.via_bot else None
            )
            return

        # Check if user exists in database
        user = await self._user_repository.get_by_telegram_id(target_user.id)
        if not user:
            logger.warning(
                "User not found in database for @HowGayBot message",
                telegram_user_id=target_user.id,
                username=target_user.username
            )
            return

        # Process title update
        try:
            message_date = message.date.date() if message.date else date.today()
            await self._update_title_use_case.execute(
                telegram_user_id=user.telegram_user_id,
                percentage=percentage,
                message_date=message_date
            )
            logger.info(
                "Title updated from @HowGayBot message",
                user_id=user.id,
                telegram_user_id=user.telegram_user_id,
                percentage=int(percentage),
                new_title=str(user.title)
            )
        except TitleLockedError:
            logger.info(
                "Title update skipped - title is locked",
                user_id=user.id,
                telegram_user_id=user.telegram_user_id
            )
        except UserNotFoundError as e:
            logger.error(
                "User not found during title update",
                error=str(e),
                telegram_user_id=user.telegram_user_id
            )
        except Exception as e:
            logger.error(
                "Error processing @HowGayBot message",
                error=str(e),
                telegram_user_id=user.telegram_user_id,
                exc_info=True
            )

    async def _identify_target_user(self, message) -> Optional:
        """
        Identify target user from message context.
        
        Strategy for messages via @HowGayBot:
        1. Primary: Use message.from_user (the actual user who sent the message via bot)
        2. Fallback: Check if message is a reply (use reply_to_message.from_user)
        
        For messages directly from @HowGayBot (not via):
        1. Primary: Check if message is a reply (use reply_to_message.from_user)
        
        Returns:
            Target user (from_user) or None if cannot identify
        """
        # If message is sent via @HowGayBot, the from_user is the actual user
        if message.via_bot and message.via_bot.username == "HowGayBot":
            if message.from_user:
                return message.from_user
        
        # Otherwise, check if message is a reply (for direct messages from HowGayBot)
        if message.reply_to_message and message.reply_to_message.from_user:
            return message.reply_to_message.from_user
        
        return None
