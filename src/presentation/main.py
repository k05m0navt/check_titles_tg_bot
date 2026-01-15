"""Main entry point for Telegram bot application."""

import asyncio
import os
import signal
import structlog
from telegram import BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler as TelegramMessageHandler, CallbackQueryHandler, InlineQueryHandler as TelegramInlineQueryHandler, filters
from telegram.error import Conflict

from src.infrastructure.config.settings import settings as app_settings
from src.infrastructure.database.supabase_client import SupabaseClient
from src.infrastructure.logging.logger import configure_logging, get_logger
from src.infrastructure.jobs.scheduler import JobScheduler
from src.infrastructure.jobs.daily_snapshot_job import DailySnapshotJob

# Repository implementations
from src.infrastructure.database.repositories.supabase_user_repository import SupabaseUserRepository
from src.infrastructure.database.repositories.supabase_statistics_repository import SupabaseStatisticsRepository
from src.infrastructure.database.repositories.supabase_title_history_repository import SupabaseTitleHistoryRepository
from src.infrastructure.database.repositories.supabase_settings_repository import SupabaseSettingsRepository

# Use cases
from src.application.use_cases.update_title_use_case import UpdateTitleUseCase, UserRepositoryActiveCounter
from src.application.use_cases.get_user_stats_use_case import GetUserStatsUseCase
from src.application.use_cases.get_leaderboard_use_case import GetLeaderboardUseCase
from src.application.use_cases.calculate_statistics_use_case import CalculateStatisticsUseCase
from src.application.use_cases.lock_title_use_case import LockTitleUseCase
from src.application.use_cases.unlock_title_use_case import UnlockTitleUseCase
from src.application.use_cases.set_full_title_use_case import SetFullTitleUseCase
from src.application.use_cases.set_full_title_for_all_use_case import SetFullTitleForAllUseCase
from src.application.use_cases.set_global_average_period_use_case import SetGlobalAveragePeriodUseCase
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.add_user_use_case import AddUserUseCase
from src.application.use_cases.set_default_title_use_case import SetDefaultTitleUseCase
from src.application.use_cases.migrate_users_to_default_title_use_case import MigrateUsersToDefaultTitleUseCase
from src.application.use_cases.delete_user_use_case import DeleteUserUseCase

# Services
from src.application.services.message_parser import MessageParser
from src.application.services.admin_service import AdminService
from src.domain.services.title_calculation_service import TitleCalculationService
from src.infrastructure.telegram.telegram_user_resolver import TelegramUserResolver

# Handlers
from src.presentation.handlers.command_handlers import CommandHandlers
from src.presentation.handlers.message_handler import MessageHandler
from src.presentation.handlers.callback_handler import CallbackHandler
from src.presentation.handlers.inline_query_handler import InlineQueryHandler
from src.presentation.handlers.chat_member_handler import ChatMemberHandler
from src.presentation.errors.error_handler import error_handler

# Configure structured logging
configure_logging(log_level="INFO")
logger = get_logger(__name__)


def setup_dependencies(bot_instance=None):
    """Setup and wire all dependencies.
    
    Args:
        bot_instance: Telegram Bot instance (optional, required for TelegramUserResolver)
    """
    # Validate settings
    app_settings.validate()

    # Create repositories
    user_repository = SupabaseUserRepository()
    statistics_repository = SupabaseStatisticsRepository()
    title_history_repository = SupabaseTitleHistoryRepository()
    settings_repository = SupabaseSettingsRepository()

    # Create services
    admin_service = AdminService()
    active_user_counter = UserRepositoryActiveCounter(user_repository)
    title_calculation_service = TitleCalculationService(active_user_counter)
    
    # Create TelegramUserResolver if bot_instance is available
    telegram_user_resolver = None
    if bot_instance:
        telegram_user_resolver = TelegramUserResolver(bot_instance=bot_instance)

    # Create use cases
    update_title_use_case = UpdateTitleUseCase(
        user_repository=user_repository,
        statistics_repository=statistics_repository,
        title_history_repository=title_history_repository,
        title_calculation_service=title_calculation_service,
        settings_repository=settings_repository,
    )

    get_leaderboard_use_case = GetLeaderboardUseCase(user_repository=user_repository)

    get_user_stats_use_case = GetUserStatsUseCase(
        user_repository=user_repository,
        statistics_repository=statistics_repository,
        title_history_repository=title_history_repository,
        get_leaderboard_use_case=get_leaderboard_use_case,
    )

    calculate_statistics_use_case = CalculateStatisticsUseCase(
        statistics_repository=statistics_repository,
        settings_repository=settings_repository,
    )

    lock_title_use_case = LockTitleUseCase(
        user_repository=user_repository,
        admin_service=admin_service,
    )

    unlock_title_use_case = UnlockTitleUseCase(
        user_repository=user_repository,
        admin_service=admin_service,
    )

    set_full_title_use_case = SetFullTitleUseCase(
        user_repository=user_repository,
        title_history_repository=title_history_repository,
        title_calculation_service=title_calculation_service,
    )

    set_full_title_for_all_use_case = SetFullTitleForAllUseCase(
        user_repository=user_repository,
        title_history_repository=title_history_repository,
        title_calculation_service=title_calculation_service,
    )

    set_global_average_period_use_case = SetGlobalAveragePeriodUseCase(
        settings_repository=settings_repository,
        admin_service=admin_service,
    )

    # Create new use cases for user registration and default title
    register_user_use_case = RegisterUserUseCase(
        user_repository=user_repository,
        settings_repository=settings_repository,
    )

    set_default_title_use_case = SetDefaultTitleUseCase(
        settings_repository=settings_repository,
        admin_service=admin_service,
    )

    migrate_users_to_default_title_use_case = MigrateUsersToDefaultTitleUseCase(
        user_repository=user_repository,
        settings_repository=settings_repository,
        title_calculation_service=title_calculation_service,
        admin_service=admin_service,
    )

    delete_user_use_case = DeleteUserUseCase(
        user_repository=user_repository,
        admin_service=admin_service,
    )

    # Create AddUserUseCase if telegram_user_resolver is available
    add_user_use_case = None
    if telegram_user_resolver:
        add_user_use_case = AddUserUseCase(
            telegram_user_resolver=telegram_user_resolver,
            register_user_use_case=register_user_use_case,
            user_repository=user_repository,
            admin_service=admin_service,
        )

    # Create jobs
    daily_snapshot_job = DailySnapshotJob(
        user_repository=user_repository,
        statistics_repository=statistics_repository,
    )

    # Create scheduler (started after bot starts)
    scheduler = JobScheduler(daily_snapshot_job=daily_snapshot_job)

    # Create handlers
    command_handlers = CommandHandlers(
        user_repository=user_repository,
        settings_repository=settings_repository,
        get_user_stats_use_case=get_user_stats_use_case,
        get_leaderboard_use_case=get_leaderboard_use_case,
        calculate_statistics_use_case=calculate_statistics_use_case,
        lock_title_use_case=lock_title_use_case,
        unlock_title_use_case=unlock_title_use_case,
        set_full_title_use_case=set_full_title_use_case,
        set_full_title_for_all_use_case=set_full_title_for_all_use_case,
        set_global_average_period_use_case=set_global_average_period_use_case,
        register_user_use_case=register_user_use_case,
        add_user_use_case=add_user_use_case,  # May be None if bot_instance not available yet
        set_default_title_use_case=set_default_title_use_case,
        migrate_users_to_default_title_use_case=migrate_users_to_default_title_use_case,
        delete_user_use_case=delete_user_use_case,
        admin_service=admin_service,
    )

    message_handler = MessageHandler(
        user_repository=user_repository,
        update_title_use_case=update_title_use_case,
    )

    callback_handler = CallbackHandler(
        user_repository=user_repository,
        get_user_stats_use_case=get_user_stats_use_case,
        get_leaderboard_use_case=get_leaderboard_use_case,
        admin_service=admin_service,
    )

    inline_query_handler = InlineQueryHandler(
        user_repository=user_repository,
        admin_service=admin_service,
    )

    chat_member_handler = ChatMemberHandler(user_repository=user_repository)

    return {
        "command_handlers": command_handlers,
        "message_handler": message_handler,
        "callback_handler": callback_handler,
        "inline_query_handler": inline_query_handler,
        "chat_member_handler": chat_member_handler,
        "scheduler": scheduler,
        "add_user_use_case": add_user_use_case,  # Return for potential updates
    }


async def main():
    """Main application entry point."""
    logger.info("Starting Telegram bot application")

    # Check for other running instances (warn only, don't block)
    import subprocess
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=2
        )
        bot_processes = [
            line for line in result.stdout.split('\n')
            if 'python' in line.lower() and 'bot' in line.lower() and 'grep' not in line
            and ('src.presentation.main' in line or 'bot.py' in line or 'main.py' in line)
        ]
        # Filter out current process
        bot_processes = [p for p in bot_processes if str(os.getpid()) not in p]
        
        if bot_processes:
            logger.warning(
                f"⚠️  Found {len(bot_processes)} other bot process(es) that might be running:"
            )
            for proc in bot_processes[:3]:  # Show first 3
                logger.warning(f"   {proc.strip()[:100]}")
            logger.warning(
                "   If you get Conflict errors, stop these processes first:"
            )
            logger.warning("   pkill -f 'python.*bot' && pkill -f 'src.presentation.main'")
    except Exception:
        # If ps command fails, skip the check
        pass

    # Test database connection
    try:
        await SupabaseClient.test_connection()
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(
            f"Database connection failed: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        # Provide helpful error message based on exception type
        if "SUPABASE_URL" in str(e) or "SUPABASE_KEY" in str(e) or not app_settings.SUPABASE_URL or not app_settings.SUPABASE_KEY:
            logger.error("Missing Supabase environment variables. Please set SUPABASE_URL and SUPABASE_KEY")
        raise ConnectionError(f"Database connection failed: {str(e)}") from e

    # Create Telegram application (app.bot is available after build())
    app = ApplicationBuilder().token(app_settings.TELEGRAM_BOT_TOKEN).build()

    # Setup dependencies (after app.bot is available for TelegramUserResolver)
    handlers = setup_dependencies(bot_instance=app.bot)

    # Register command handlers
    app.add_handler(CommandHandler("start", handlers["command_handlers"].handle_start))
    app.add_handler(CommandHandler("register", handlers["command_handlers"].handle_register))
    app.add_handler(CommandHandler("me", handlers["command_handlers"].handle_me))
    app.add_handler(CommandHandler("who", handlers["command_handlers"].handle_who))
    app.add_handler(CommandHandler("leaderboard", handlers["command_handlers"].handle_leaderboard))
    app.add_handler(CommandHandler("stats", handlers["command_handlers"].handle_stats))
    app.add_handler(CommandHandler("help", handlers["command_handlers"].handle_help))
    app.add_handler(CommandHandler("chat_id", handlers["command_handlers"].handle_chat_id))
    app.add_handler(CommandHandler("add_user", handlers["command_handlers"].handle_add_user))
    app.add_handler(CommandHandler("set_default_title", handlers["command_handlers"].handle_set_default_title))
    app.add_handler(CommandHandler("migrate_users_to_default_title", handlers["command_handlers"].handle_migrate_users_to_default_title))
    app.add_handler(CommandHandler("lock_title", handlers["command_handlers"].handle_lock_title))
    app.add_handler(CommandHandler("unlock_title", handlers["command_handlers"].handle_unlock_title))
    app.add_handler(CommandHandler("set_full_title", handlers["command_handlers"].handle_set_full_title))
    app.add_handler(CommandHandler("set_title", handlers["command_handlers"].handle_set_full_title))  # Alias for set_full_title
    app.add_handler(CommandHandler("set_full_title_for_all", handlers["command_handlers"].handle_set_full_title_for_all))
    app.add_handler(CommandHandler("set_global_average_period", handlers["command_handlers"].handle_set_global_average_period))
    app.add_handler(CommandHandler("delete_user", handlers["command_handlers"].handle_delete_user))

    # Register message handler (filter for group messages to monitor @HowGayBot)
    app.add_handler(
        TelegramMessageHandler(
            filters.TEXT & (~filters.COMMAND),
            handlers["message_handler"].handle_message
        )
    )

    # Register callback query handler
    app.add_handler(CallbackQueryHandler(handlers["callback_handler"].handle_callback))

    # Register inline query handler
    app.add_handler(TelegramInlineQueryHandler(handlers["inline_query_handler"].handle_inline_query))

    # Register chat member handler for bot-added-to-group events
    app.add_handler(
        TelegramMessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            handlers["chat_member_handler"].handle_new_chat_members
        )
    )

    # Register global error handler
    app.add_error_handler(error_handler)

    logger.info("Bot application configured, starting polling")
    
    # Create a stop event to signal shutdown
    stop_event = asyncio.Event()
    
    # Setup signal handlers for graceful shutdown
    def handle_shutdown(signum=None, frame=None):
        """Handle shutdown signals."""
        logger.info(f"Received shutdown signal ({signum or 'KeyboardInterrupt'}), initiating graceful shutdown...")
        stop_event.set()
    
    # Setup signal handlers (Unix/Linux/Mac)
    try:
        loop = asyncio.get_running_loop()
        if hasattr(signal, 'SIGTERM'):
            loop.add_signal_handler(signal.SIGTERM, handle_shutdown)
        loop.add_signal_handler(signal.SIGINT, handle_shutdown)
    except (NotImplementedError, RuntimeError, AttributeError):
        # Fallback for Windows or platforms without signal support
        signal.signal(signal.SIGINT, handle_shutdown)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Use context manager for proper lifecycle management
    # This automatically handles initialize() and shutdown()
    async with app:
        # Initialize and start application
        await app.start()
        
        # Ensure webhook is deleted (in case one was set previously)
        # This is necessary to avoid conflicts with polling
        try:
            webhook_info = await app.bot.get_webhook_info()
            if webhook_info.url:
                logger.warning(f"Webhook detected: {webhook_info.url}. Deleting it...")
                await app.bot.delete_webhook(drop_pending_updates=True)
                logger.info("Webhook deleted successfully")
            else:
                logger.info("No webhook configured, ready for polling")
        except Exception as e:
            logger.warning("Could not check/delete webhook", error=str(e))
            # Try to delete anyway
            try:
                await app.bot.delete_webhook(drop_pending_updates=True)
            except Exception:
                pass  # Ignore if it fails
        
        # Register bot commands with Telegram API (so they appear in the menu)
        try:
            commands = [
                BotCommand("start", "Start the bot"),
                BotCommand("register", "Register yourself with the bot"),
                BotCommand("me", "Show your stats"),
                BotCommand("who", "Show user stats"),
                BotCommand("leaderboard", "Show leaderboard"),
                BotCommand("stats", "Show statistics"),
                BotCommand("chat_id", "Show current chat ID"),
                BotCommand("help", "Show help message"),
            ]
            await app.bot.set_my_commands(commands)
            logger.info("Bot commands registered with Telegram API")
        except Exception as e:
            logger.warning(f"Could not register bot commands: {str(e)}")
        
        # Small delay to allow any previous instance to fully shut down
        # This helps avoid transient conflicts during container restarts
        await asyncio.sleep(2)
        
        # Start polling with error handling and retry logic
        max_retries = 3
        retry_delay = 5  # seconds
        polling_started = False
        
        for attempt in range(1, max_retries + 1):
            try:
                await app.updater.start_polling(drop_pending_updates=True)
                logger.info("Bot polling started successfully")
                polling_started = True
                break
            except Conflict as e:
                if attempt < max_retries:
                    logger.warning(
                        f"⚠️  Bot conflict detected (attempt {attempt}/{max_retries}). "
                        f"Another instance may still be shutting down. Retrying in {retry_delay}s...",
                        error=str(e)
                    )
                    await asyncio.sleep(retry_delay)
                    # Double the delay for next retry (exponential backoff)
                    retry_delay *= 2
                else:
                    logger.error(
                        "❌ Bot conflict error - another instance is already polling for updates after all retries",
                        error=str(e)
                    )
                    logger.error(
                        "💡 Solution: Stop all other bot instances before starting this one."
                    )
                    logger.info("   To find running instances:")
                    logger.info("     ps aux | grep 'python.*bot' | grep -v grep")
                    logger.info("   Or check for all Python bot processes:")
                    logger.info("     pkill -f 'python.*bot'")
                    logger.info("     pkill -f 'src.presentation.main'")
                    raise
        
        if not polling_started:
            raise RuntimeError("Failed to start polling after all retries")
        
        # Start scheduler (after polling starts)
        handlers["scheduler"].start()
        logger.info("Job scheduler started")
        
        logger.info("Bot is running. Press Ctrl+C to stop.")
        
        try:
            # Keep the event loop running until stop_event is set
            await stop_event.wait()
        finally:
            # Shutdown in reverse order
            logger.info("Shutting down...")
            handlers["scheduler"].shutdown()
            logger.info("Job scheduler stopped")
            
            await app.updater.stop()
            await app.stop()
            logger.info("Bot application shut down")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Final fallback for KeyboardInterrupt at the top level
        print("\n✓ Shutdown complete")
