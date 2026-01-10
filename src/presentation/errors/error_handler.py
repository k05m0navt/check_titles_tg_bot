"""Global error handler for Telegram bot."""

import structlog
from telegram import Update
from telegram.ext import ContextTypes

from ...domain.exceptions import (
    DomainError,
    TitleLockedError,
    InvalidPercentageError,
    UserNotFoundError,
    InvalidTimezoneError,
)
from ...infrastructure.config.settings import settings as app_settings
from ..utils.localization import get_user_language
from ...infrastructure.i18n.translations import translate

logger = structlog.get_logger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler for Telegram updates."""
    error = context.error

    # Log error
    logger.error(
        "Error in Telegram update",
        error=str(error),
        error_type=type(error).__name__,
        update_id=update.update_id if update else None,
        exc_info=error
    )

    # Map domain exceptions to user-friendly messages
    if isinstance(error, UserNotFoundError):
        user_message = translate("errors.user_not_found", "en")  # Default to English
        if update and update.message:
            await update.message.reply_text(user_message)
        return

    if isinstance(error, TitleLockedError):
        user_message = translate("errors.title_locked", "en")
        if update and update.message:
            await update.message.reply_text(user_message)
        return

    if isinstance(error, InvalidPercentageError):
        user_message = translate("errors.invalid_percentage", "en")
        if update and update.message:
            await update.message.reply_text(user_message)
        return

    if isinstance(error, PermissionError):
        user_message = translate("errors.permission_denied", "en")
        if update and update.message:
            await update.message.reply_text(user_message)
        return

    # Generic error message for other errors (don't expose internal errors)
    if update and update.message:
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )

    # Notify admin on critical errors (if configured)
    if app_settings.ADMIN_USER_ID:
        try:
            # Would need bot instance to send DM to admin
            # For now, just log it
            logger.warning(
                "Critical error - admin should be notified",
                admin_user_id=app_settings.ADMIN_USER_ID,
                error=str(error)
            )
        except Exception:
            logger.error("Failed to notify admin", exc_info=True)
