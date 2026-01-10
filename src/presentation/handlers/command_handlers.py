"""Command handlers for Telegram bot."""

from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

from ...domain.repositories.user_repository import IUserRepository
from ...domain.repositories.settings_repository import ISettingsRepository
from ...domain.exceptions import UserNotFoundError
from ...application.use_cases.get_user_stats_use_case import GetUserStatsUseCase
from ...application.use_cases.get_leaderboard_use_case import GetLeaderboardUseCase
from ...application.use_cases.calculate_statistics_use_case import CalculateStatisticsUseCase
from ...application.use_cases.lock_title_use_case import LockTitleUseCase
from ...application.use_cases.unlock_title_use_case import UnlockTitleUseCase
from ...application.use_cases.set_full_title_use_case import SetFullTitleUseCase
from ...application.use_cases.set_global_average_period_use_case import SetGlobalAveragePeriodUseCase
from ...application.use_cases.register_user_use_case import RegisterUserUseCase
from ...application.use_cases.add_user_use_case import AddUserUseCase
from ...application.use_cases.set_default_title_use_case import SetDefaultTitleUseCase
from ...application.use_cases.migrate_users_to_default_title_use_case import MigrateUsersToDefaultTitleUseCase
from ...application.use_cases.delete_user_use_case import DeleteUserUseCase
from ...application.services.admin_service import AdminService
from ..keyboards.inline_keyboard_builder import InlineKeyboardBuilder
from ..utils.localization import get_user_language, format_translated_message_async
from ...infrastructure.i18n.translations import translate


class CommandHandlers:
    """Command handlers for bot commands."""

    def __init__(
        self,
        user_repository: IUserRepository,
        settings_repository: ISettingsRepository,
        get_user_stats_use_case: GetUserStatsUseCase,
        get_leaderboard_use_case: GetLeaderboardUseCase,
        calculate_statistics_use_case: CalculateStatisticsUseCase,
        lock_title_use_case: LockTitleUseCase,
        unlock_title_use_case: UnlockTitleUseCase,
        set_full_title_use_case: SetFullTitleUseCase,
        set_global_average_period_use_case: SetGlobalAveragePeriodUseCase,
        register_user_use_case: RegisterUserUseCase,
        add_user_use_case: AddUserUseCase,
        set_default_title_use_case: SetDefaultTitleUseCase,
        migrate_users_to_default_title_use_case: MigrateUsersToDefaultTitleUseCase,
        delete_user_use_case: DeleteUserUseCase,
        admin_service: AdminService,
    ):
        """Initialize command handlers with dependencies."""
        self._user_repository = user_repository
        self._settings_repository = settings_repository
        self._get_user_stats_use_case = get_user_stats_use_case
        self._get_leaderboard_use_case = get_leaderboard_use_case
        self._calculate_statistics_use_case = calculate_statistics_use_case
        self._lock_title_use_case = lock_title_use_case
        self._unlock_title_use_case = unlock_title_use_case
        self._set_full_title_use_case = set_full_title_use_case
        self._set_global_average_period_use_case = set_global_average_period_use_case
        self._register_user_use_case = register_user_use_case
        self._add_user_use_case = add_user_use_case
        self._set_default_title_use_case = set_default_title_use_case
        self._migrate_users_to_default_title_use_case = migrate_users_to_default_title_use_case
        self._delete_user_use_case = delete_user_use_case
        self._admin_service = admin_service

    async def handle_me(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /me command."""
        user = update.message.from_user
        language = await get_user_language(self._user_repository, user.id)

        stats = await self._get_user_stats_use_case.execute(user.id)
        if not stats:
            await update.message.reply_text(
                translate("messages.not_in_table", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=self._admin_service.is_admin(user.id, user.username),
                    language=language
                )
            )
            return

        # Format stats message
        stats_text = f"📊 {translate('stats.user_stats', language)}\n\n"
        stats_text += f"{translate('stats.title', language)}: {stats.title}\n"
        stats_text += f"{translate('stats.percentage', language)}: {stats.current_percentage}%\n" if stats.current_percentage else ""
        stats_text += f"{translate('stats.position', language)}: #{stats.position_in_leaderboard}\n" if stats.position_in_leaderboard else ""
        
        if stats.daily_trend:
            stats_text += f"Daily: {stats.daily_trend:.1f}%\n"
        if stats.weekly_trend:
            stats_text += f"Weekly: {stats.weekly_trend:.1f}%\n"
        if stats.monthly_trend:
            stats_text += f"Monthly: {stats.monthly_trend:.1f}%\n"

        await update.message.reply_text(
            stats_text,
            reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                is_admin=self._admin_service.is_admin(user.id, user.username),
                language=language
            )
        )

    async def handle_who(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /who @username command."""
        user = update.message.from_user
        language = await get_user_language(self._user_repository, user.id)
        is_admin = self._admin_service.is_admin(user.id, user.username)
        
        if not context.args:
            await update.message.reply_text(
                f"{translate('commands.who', language)}: /who @username",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        username = context.args[0].replace("@", "")

        target_user = await self._user_repository.get_by_username(username)
        if not target_user:
            await update.message.reply_text(
                translate("errors.user_not_found", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        stats = await self._get_user_stats_use_case.execute(target_user.telegram_user_id)
        if not stats:
            await update.message.reply_text(
                translate("errors.user_not_found", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        user = update.message.from_user
        is_admin = self._admin_service.is_admin(user.id, user.username)
        
        stats_text = f"👤 {username}\n"
        stats_text += f"{translate('stats.title', language)}: {stats.title}\n"
        stats_text += f"{translate('stats.percentage', language)}: {stats.current_percentage}%\n" if stats.current_percentage else ""
        stats_text += f"{translate('stats.position', language)}: #{stats.position_in_leaderboard}\n" if stats.position_in_leaderboard else ""

        await update.message.reply_text(
            stats_text,
            reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                is_admin=is_admin,
                language=language
            )
        )

    async def handle_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /leaderboard command."""
        user = update.message.from_user
        language = await get_user_language(self._user_repository, user.id)
        is_admin = self._admin_service.is_admin(user.id, user.username)

        entries = await self._get_leaderboard_use_case.execute(limit=10, sort_order="asc")

        if not entries:
            await update.message.reply_text(
                translate("messages.not_in_table", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        leaderboard_text = f"👥 {translate('commands.leaderboard', language)}\n\n"
        for entry in entries:
            username = entry.telegram_username or entry.display_name or "Unknown"
            leaderboard_text += f"{entry.position}. @{username} - {entry.title} ({entry.title_letter_count})\n"

        await update.message.reply_text(
            leaderboard_text,
            reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                is_admin=is_admin,
                language=language
            )
        )

    async def handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats [range] command."""
        user = update.message.from_user
        language = await get_user_language(self._user_repository, user.id)
        is_admin = self._admin_service.is_admin(user.id, user.username)

        period_days = None
        if context.args:
            try:
                period_days = int(context.args[0])
            except ValueError:
                pass

        global_avg = await self._calculate_statistics_use_case.execute(period_days)

        stats_text = f"📊 {translate('stats.global_average', language)}\n"
        if global_avg is not None:
            stats_text += f"{global_avg:.2f}%"
        else:
            stats_text += "No data available"

        await update.message.reply_text(
            stats_text,
            reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                is_admin=is_admin,
                language=language
            )
        )

    async def handle_lock_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /lock_title @username command (admin only)."""
        user = update.message.from_user
        language = await get_user_language(self._user_repository, user.id)
        is_admin = self._admin_service.is_admin(user.id, user.username)

        if not context.args:
            await update.message.reply_text(
                f"{translate('commands.lock_title', language)}: /lock_title @username",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        if not is_admin:
            await update.message.reply_text(
                translate("errors.permission_denied", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=False,
                    language=language
                )
            )
            return

        username = context.args[0].replace("@", "")
        target_user = await self._user_repository.get_by_username(username)
        if not target_user:
            await update.message.reply_text(
                translate("errors.user_not_found", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        try:
            await self._lock_title_use_case.execute(
                target_user.telegram_user_id,
                user.id,
                user.username
            )
            await update.message.reply_text(
                f"{translate('messages.title_locked', language)} @{username}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except Exception as e:
            await update.message.reply_text(
                f"Error: {str(e)}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )

    async def handle_unlock_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unlock_title @username command (admin only)."""
        user = update.message.from_user
        language = await get_user_language(self._user_repository, user.id)
        is_admin = self._admin_service.is_admin(user.id, user.username)

        if not context.args:
            await update.message.reply_text(
                f"{translate('commands.unlock_title', language)}: /unlock_title @username",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        if not is_admin:
            await update.message.reply_text(
                translate("errors.permission_denied", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=False,
                    language=language
                )
            )
            return

        username = context.args[0].replace("@", "")
        target_user = await self._user_repository.get_by_username(username)
        if not target_user:
            await update.message.reply_text(
                translate("errors.user_not_found", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        try:
            await self._unlock_title_use_case.execute(
                target_user.telegram_user_id,
                user.id,
                user.username
            )
            await update.message.reply_text(
                f"{translate('messages.title_unlocked', language)} @{username}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except Exception as e:
            await update.message.reply_text(
                f"Error: {str(e)}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )

    async def handle_set_full_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /set_full_title @username <full_title> command (admin only)."""
        user = update.message.from_user
        language = await get_user_language(self._user_repository, user.id)
        is_admin = self._admin_service.is_admin(user.id, user.username)

        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                f"{translate('commands.set_full_title', language)}: /set_full_title @username <full_title>",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        if not is_admin:
            await update.message.reply_text(
                translate("errors.permission_denied", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=False,
                    language=language
                )
            )
            return

        username = context.args[0].replace("@", "")
        full_title = " ".join(context.args[1:])  # Join remaining args as full_title (may contain spaces)

        target_user = await self._user_repository.get_by_username(username)
        if not target_user:
            await update.message.reply_text(
                translate("errors.user_not_found", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        try:
            await self._set_full_title_use_case.execute(
                target_user.telegram_user_id,
                full_title,
                user.id,
                user.username
            )
            await update.message.reply_text(
                f"✅ Full title set for @{username}: '{full_title}'",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except PermissionError as e:
            await update.message.reply_text(
                translate("errors.permission_denied", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except Exception as e:
            await update.message.reply_text(
                f"Error: {str(e)}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )

    async def handle_set_global_average_period(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /set_global_average_period <days> command (admin only)."""
        user = update.message.from_user
        language = await get_user_language(self._user_repository, user.id)
        is_admin = self._admin_service.is_admin(user.id, user.username)

        if not context.args:
            await update.message.reply_text(
                f"{translate('commands.set_global_average_period', language)}: /set_global_average_period <days>",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        if not is_admin:
            await update.message.reply_text(
                translate("errors.permission_denied", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=False,
                    language=language
                )
            )
            return

        try:
            period_days = int(context.args[0])
            await self._set_global_average_period_use_case.execute(
                period_days, user.id, user.username
            )
            await update.message.reply_text(
                f"✅ Global average period set to {period_days} days (0 = all-time)",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except ValueError:
            await update.message.reply_text(
                "Invalid number format",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except Exception as e:
            await update.message.reply_text(
                f"Error: {str(e)}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.message.from_user
        language = await get_user_language(self._user_repository, user.id)
        is_admin = self._admin_service.is_admin(user.id, user.username)
        
        welcome_text = f"👋 {translate('commands.welcome', language)}\n\n"
        welcome_text += f"{translate('commands.available_commands', language)}:\n"
        welcome_text += f"• /register - Register yourself with the bot\n"
        welcome_text += f"• /me - {translate('commands.me', language)}\n"
        welcome_text += f"• /who @username - {translate('commands.who', language)}\n"
        welcome_text += f"• /leaderboard - {translate('commands.leaderboard', language)}\n"
        welcome_text += f"• /stats [days] - {translate('commands.stats', language)}\n"
        welcome_text += f"• /help - Show help message\n"
        
        if is_admin:
            welcome_text += f"\n🔧 {translate('commands.admin_commands', language)}:\n"
            welcome_text += f"• /add_user @username <chat_id> - Add user manually\n"
            welcome_text += f"• /delete_user @username - Delete user\n"
            welcome_text += f"• /set_default_title <title> - Set default title for new users\n"
            welcome_text += f"• /migrate_users_to_default_title - Migrate all users to default title\n"
            welcome_text += f"• /lock_title @username - {translate('commands.lock_title', language)}\n"
            welcome_text += f"• /unlock_title @username - {translate('commands.unlock_title', language)}\n"
            welcome_text += f"• /set_full_title @username <title> - {translate('commands.set_full_title', language)}\n"
            welcome_text += f"• /set_global_average_period <days> - {translate('commands.set_global_average_period', language)}\n"
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                is_admin=is_admin,
                language=language
            )
        )

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        user = update.message.from_user
        language = await get_user_language(self._user_repository, user.id)
        is_admin = self._admin_service.is_admin(user.id, user.username)
        
        help_text = translate("commands.help", language)
        await update.message.reply_text(
            help_text,
            reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                is_admin=is_admin,
                language=language
            )
        )

    async def handle_register(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /register command."""
        user = update.message.from_user
        language = await get_user_language(self._user_repository, user.id)
        is_admin = self._admin_service.is_admin(user.id, user.username)

        try:
            was_created = await self._register_user_use_case.execute(
                telegram_user_id=user.id,
                telegram_username=user.username,
                display_name=user.full_name,
            )
            
            if was_created:
                # User was just created - check if default title is set
                default_title = await self._settings_repository.get_default_title()
                if default_title and default_title.strip():
                    message = "✅ Registration successful! Your default title is set. Use /me to check your stats."
                else:
                    message = "✅ Registration successful! Note: Default title not set by admin yet."
            else:
                # User already existed (idempotent)
                message = "✅ You're already registered! Use /me to check your stats."
                
            await update.message.reply_text(
                message,
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except ValueError as e:
            await update.message.reply_text(
                f"❌ Registration failed: {str(e)}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except ConnectionError as e:
            await update.message.reply_text(
                "❌ Registration failed due to a temporary issue. Please try again later.",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Registration failed: {str(e)}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )

    async def handle_add_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add_user @username <chat_id> command (admin only)."""
        user = update.message.from_user
        language = await get_user_language(self._user_repository, user.id)
        is_admin = self._admin_service.is_admin(user.id, user.username)

        if not is_admin:
            await update.message.reply_text(
                translate("errors.permission_denied", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=False,
                    language=language
                )
            )
            return

        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ Usage: /add_user @username <chat_id>. Chat ID is required because Telegram API cannot resolve username without chat context.",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        username = context.args[0].replace("@", "")
        try:
            chat_id = int(context.args[1])
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid chat_id. Must be a valid integer.",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        try:
            was_created = await self._add_user_use_case.execute(
                username=username,
                chat_id=chat_id,
                admin_user_id=user.id,
                admin_username=user.username,
            )
            
            if was_created:
                message = f"✅ User @{username} added successfully!"
            else:
                message = f"✅ User @{username} is already registered."
                
            await update.message.reply_text(
                message,
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except PermissionError:
            await update.message.reply_text(
                translate("errors.permission_denied", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except UserNotFoundError as e:
            await update.message.reply_text(
                f"❌ {str(e)}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except ValueError as e:
            await update.message.reply_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Unexpected error: {str(e)}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )

    async def handle_set_default_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /set_default_title <title> command (admin only)."""
        user = update.message.from_user
        language = await get_user_language(self._user_repository, user.id)
        is_admin = self._admin_service.is_admin(user.id, user.username)

        if not is_admin:
            await update.message.reply_text(
                translate("errors.permission_denied", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=False,
                    language=language
                )
            )
            return

        if not context.args:
            await update.message.reply_text(
                "❌ Usage: /set_default_title <title>. Title can contain spaces.",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        default_title = " ".join(context.args)  # Join all args as title (may contain spaces)

        try:
            message = await self._set_default_title_use_case.execute(
                default_title=default_title,
                admin_user_id=user.id,
                admin_username=user.username,
            )
            await update.message.reply_text(
                f"✅ {message}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except PermissionError:
            await update.message.reply_text(
                translate("errors.permission_denied", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except ValueError as e:
            await update.message.reply_text(
                f"❌ {str(e)}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )

    async def handle_migrate_users_to_default_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /migrate_users_to_default_title command (admin only)."""
        user = update.message.from_user
        language = await get_user_language(self._user_repository, user.id)
        is_admin = self._admin_service.is_admin(user.id, user.username)

        if not is_admin:
            await update.message.reply_text(
                translate("errors.permission_denied", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=False,
                    language=language
                )
            )
            return

        try:
            updated_count = await self._migrate_users_to_default_title_use_case.execute(
                admin_user_id=user.id,
                admin_username=user.username,
            )
            await update.message.reply_text(
                f"✅ Migrated {updated_count} users to default title.",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except PermissionError:
            await update.message.reply_text(
                translate("errors.permission_denied", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except ValueError as e:
            await update.message.reply_text(
                f"❌ {str(e)}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )

    async def handle_delete_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /delete_user @username command (admin only)."""
        user = update.message.from_user
        language = await get_user_language(self._user_repository, user.id)
        is_admin = self._admin_service.is_admin(user.id, user.username)

        if not context.args:
            await update.message.reply_text(
                f"Delete user: /delete_user @username",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        if not is_admin:
            await update.message.reply_text(
                translate("errors.permission_denied", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=False,
                    language=language
                )
            )
            return

        username = context.args[0].replace("@", "")
        target_user = await self._user_repository.get_by_username(username)
        if not target_user:
            await update.message.reply_text(
                translate("errors.user_not_found", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
            return

        try:
            await self._delete_user_use_case.execute(
                target_user.telegram_user_id,
                user.id,
                user.username
            )
            await update.message.reply_text(
                f"✅ User @{username} has been deleted successfully.",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except PermissionError:
            await update.message.reply_text(
                translate("errors.permission_denied", language),
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except UserNotFoundError as e:
            await update.message.reply_text(
                f"❌ {str(e)}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardBuilder.build_main_keyboard(
                    is_admin=is_admin,
                    language=language
                )
            )
