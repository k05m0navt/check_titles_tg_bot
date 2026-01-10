"""Callback query handler for inline button clicks."""

from telegram import Update
from telegram.ext import ContextTypes

from ...domain.repositories.user_repository import IUserRepository
from ...application.use_cases.get_user_stats_use_case import GetUserStatsUseCase
from ...application.use_cases.get_leaderboard_use_case import GetLeaderboardUseCase
from ...application.services.admin_service import AdminService
from ..keyboards.inline_keyboard_builder import InlineKeyboardBuilder
from ..utils.localization import get_user_language
from ...infrastructure.i18n.translations import translate


class CallbackHandler:
    """Handler for callback queries (inline button clicks)."""

    def __init__(
        self,
        user_repository: IUserRepository,
        get_user_stats_use_case: GetUserStatsUseCase,
        get_leaderboard_use_case: GetLeaderboardUseCase,
        admin_service: AdminService,
    ):
        """Initialize callback handler with dependencies."""
        self._user_repository = user_repository
        self._get_user_stats_use_case = get_user_stats_use_case
        self._get_leaderboard_use_case = get_leaderboard_use_case
        self._admin_service = admin_service

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback query."""
        query = update.callback_query
        if not query:
            return

        await query.answer()

        user = query.from_user
        language = await get_user_language(self._user_repository, user.id)
        is_admin = self._admin_service.is_admin(user.id, user.username)

        callback_data = query.data

        if callback_data == "me":
            await self._handle_me_callback(query, user, language, is_admin)
        elif callback_data == "leaderboard":
            await self._handle_leaderboard_callback(query, language, is_admin)
        elif callback_data == "help":
            await self._handle_help_callback(query, language, is_admin)
        elif callback_data == "settings":
            if is_admin:
                await self._handle_settings_callback(query, language, is_admin)
        elif callback_data == "lock_title":
            if is_admin:
                await self._handle_lock_title_callback(query, language, is_admin)
        elif callback_data == "back":
            await self._handle_back_callback(query, user, language, is_admin)

    async def _handle_me_callback(self, query, user, language: str, is_admin: bool):
        """Handle 'me' callback."""
        stats = await self._get_user_stats_use_case.execute(user.id)
        if not stats:
            await query.message.edit_text(
                translate("messages.not_in_table", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin, language=language
                )
            )
            return

        stats_text = f"📊 {translate('stats.user_stats', language)}\n\n"
        stats_text += f"{translate('stats.title', language)}: {stats.title}\n"
        if stats.current_percentage:
            stats_text += f"{translate('stats.percentage', language)}: {stats.current_percentage}%\n"
        if stats.position_in_leaderboard:
            stats_text += f"{translate('stats.position', language)}: #{stats.position_in_leaderboard}\n"

        await query.message.edit_text(
            stats_text,
            reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                is_admin=is_admin, language=language
            )
        )

    async def _handle_leaderboard_callback(self, query, language: str, is_admin: bool):
        """Handle 'leaderboard' callback."""
        entries = await self._get_leaderboard_use_case.execute(limit=10, sort_order="asc")

        if not entries:
            await query.message.edit_text(
                translate("messages.not_in_table", language),
                reply_markup=InlineKeyboardBuilder.build_back_keyboard(language)
            )
            return

        leaderboard_text = f"👥 {translate('commands.leaderboard', language)}\n\n"
        for entry in entries:
            username = entry.telegram_username or entry.display_name or "Unknown"
            leaderboard_text += f"{entry.position}. @{username} - {entry.title} ({entry.title_letter_count})\n"

        await query.message.edit_text(
            leaderboard_text,
            reply_markup=InlineKeyboardBuilder.build_back_keyboard(language)
        )

    async def _handle_help_callback(self, query, language: str, is_admin: bool):
        """Handle 'help' callback."""
        help_text = translate("commands.help", language)
        await query.message.edit_text(
            help_text,
            reply_markup=InlineKeyboardBuilder.build_back_keyboard(language)
        )

    async def _handle_settings_callback(self, query, language: str, is_admin: bool):
        """Handle 'settings' callback (admin only)."""
        settings_text = f"⚙️ {translate('buttons.settings', language)}\n\n"
        settings_text += f"{translate('commands.available_commands', language)}:\n"
        settings_text += f"• /lock_title @username - {translate('commands.lock_title', language)}\n"
        settings_text += f"• /unlock_title @username - {translate('commands.unlock_title', language)}\n"
        settings_text += f"• /set_full_title @username <title> - {translate('commands.set_full_title', language)}\n"
        settings_text += f"• /set_global_average_period <days> - {translate('commands.set_global_average_period', language)}\n"
        
        await query.message.edit_text(
            settings_text,
            reply_markup=InlineKeyboardBuilder.build_settings_keyboard(language)
        )

    async def _handle_lock_title_callback(self, query, language: str, is_admin: bool):
        """Handle 'lock_title' callback (admin only)."""
        lock_text = f"🔒 {translate('buttons.lock_title', language)}\n\n"
        lock_text += f"Use /lock_title @username to lock a user's title\n\n"
        lock_text += f"Example: /lock_title @john_doe"
        
        await query.message.edit_text(
            lock_text,
            reply_markup=InlineKeyboardBuilder.build_settings_keyboard(language)
        )
    
    async def _handle_back_callback(self, query, user, language: str, is_admin: bool):
        """Handle 'back' callback to return to main menu."""
        # Get user stats to show main menu
        stats = await self._get_user_stats_use_case.execute(user.id)
        if stats:
            stats_text = f"📊 {translate('stats.user_stats', language)}\n\n"
            stats_text += f"{translate('stats.title', language)}: {stats.title}\n"
            if stats.current_percentage:
                stats_text += f"{translate('stats.percentage', language)}: {stats.current_percentage}%\n"
            if stats.position_in_leaderboard:
                stats_text += f"{translate('stats.position', language)}: #{stats.position_in_leaderboard}\n"
            
            await query.message.edit_text(
                stats_text,
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin, language=language
                )
            )
        else:
            await query.message.edit_text(
                translate("messages.not_in_table", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin, language=language
                )
            )
