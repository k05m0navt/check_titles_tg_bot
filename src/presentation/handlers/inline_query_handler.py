"""Inline query handler for @BotName queries."""

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes

from ...domain.repositories.user_repository import IUserRepository
from ...application.services.admin_service import AdminService
from ...infrastructure.i18n.translations import translate


class InlineQueryHandler:
    """Handler for inline queries when user types @BotName."""

    def __init__(
        self,
        user_repository: IUserRepository,
        admin_service: AdminService,
    ):
        """Initialize inline query handler with dependencies."""
        self._user_repository = user_repository
        self._admin_service = admin_service

    async def handle_inline_query(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle inline query."""
        inline_query = update.inline_query
        if not inline_query:
            return

        user = inline_query.from_user
        language = "en"  # Default language for inline queries
        
        # Check if user is admin
        is_admin = self._admin_service.is_admin(user.id, user.username)

        # Build result articles
        results = [
            InlineQueryResultArticle(
                id="stats",
                title=translate("buttons.my_stats", language),
                description="Show your statistics",
                input_message_content=InputTextMessageContent("/me"),
            ),
            InlineQueryResultArticle(
                id="leaderboard",
                title=translate("buttons.leaderboard", language),
                description="Show leaderboard",
                input_message_content=InputTextMessageContent("/leaderboard"),
            ),
            InlineQueryResultArticle(
                id="help",
                title=translate("buttons.help", language),
                description="Show help message",
                input_message_content=InputTextMessageContent("/help"),
            ),
        ]

        if is_admin:
            results.append(
                InlineQueryResultArticle(
                    id="settings",
                    title=translate("buttons.settings", language),
                    description="Admin settings",
                    input_message_content=InputTextMessageContent("/help"),
                )
            )
            results.append(
                InlineQueryResultArticle(
                    id="lock_title",
                    title=translate("buttons.lock_title", language),
                    description="Lock user title (admin)",
                    input_message_content=InputTextMessageContent("/lock_title"),
                )
            )

        await inline_query.answer(results, cache_time=0)
