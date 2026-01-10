"""Translation dictionaries for localization."""

from typing import Dict

# Translation dictionaries
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # Commands
        "commands.help": (
            "📖 Bot Commands:\n\n"
            "/me - Show your stats\n"
            "/who @username - Show user stats\n"
            "/leaderboard - Show leaderboard\n"
            "/stats - Show global statistics\n"
            "/chat_id - Show current chat ID (useful for /add_user)\n"
            "/help - Show this help message\n\n"
            "Admin Commands:\n"
            "/add_user @username [chat_id] - Add user manually\n"
            "/lock_title @username - Lock user title\n"
            "/unlock_title @username - Unlock user title\n"
            "/set_global_average_period <days> - Set statistics period (0 = all-time)"
        ),
        "commands.welcome": "Welcome to the Title Tracker Bot!",
        "commands.available_commands": "Available Commands",
        "commands.admin_commands": "Admin Commands",
        "commands.me": "Show my stats",
        "commands.who": "Show user stats",
        "commands.leaderboard": "Show leaderboard",
        "commands.stats": "Show statistics",
        "commands.lock_title": "Lock user title",
        "commands.unlock_title": "Unlock user title",
        "commands.set_full_title": "Set full title for user",
        "commands.set_global_average_period": "Set global average period",
        # Errors
        "errors.user_not_found": "User not found",
        "errors.permission_denied": "❌ Permission denied. Admin access required.",
        "errors.title_locked": "Title is locked and cannot be updated automatically",
        "errors.invalid_percentage": "Invalid percentage value",
        # Messages
        "messages.title_locked": "✅ Title locked for user",
        "messages.title_unlocked": "✅ Title unlocked for user. Auto-updates enabled.",
        "messages.not_in_table": "You are not in the table 😢",
        "messages.recheck_complete": "✅ Recheck complete! Processed: {count} messages",
        # Buttons
        "buttons.my_stats": "📊 My Stats",
        "buttons.leaderboard": "👥 Leaderboard",
        "buttons.help": "📝 Help",
        "buttons.settings": "⚙️ Settings",
        "buttons.lock_title": "🔒 Lock Title",
        "buttons.back": "⬅️ Back",
        # Stats
        "stats.global_average": "Global Average",
        "stats.user_stats": "User Stats",
        "stats.position": "Position",
        "stats.title": "Title",
        "stats.percentage": "Percentage",
        # Admin
        "admin.recheck_complete": "✅ Recheck complete! Processed: {processed} messages, Updated titles: {updated} users",
    },
    "ru": {
        # Commands
        "commands.help": (
            "📖 Команды бота:\n\n"
            "/me - Показать вашу статистику\n"
            "/who @username - Показать статистику пользователя\n"
            "/leaderboard - Показать таблицу лидеров\n"
            "/stats - Показать глобальную статистику\n"
            "/chat_id - Показать ID текущего чата (полезно для /add_user)\n"
            "/help - Показать это сообщение\n\n"
            "Команды администратора:\n"
            "/add_user @username [chat_id] - Добавить пользователя вручную\n"
            "/lock_title @username - Заблокировать звание пользователя\n"
            "/unlock_title @username - Разблокировать звание пользователя\n"
            "/set_global_average_period <days> - Установить период статистики (0 = за всё время)"
        ),
        "commands.welcome": "Добро пожаловать в бота отслеживания званий!",
        "commands.available_commands": "Доступные команды",
        "commands.admin_commands": "Команды администратора",
        "commands.me": "Показать мою статистику",
        "commands.who": "Показать статистику пользователя",
        "commands.leaderboard": "Показать таблицу лидеров",
        "commands.stats": "Показать статистику",
        "commands.lock_title": "Заблокировать звание пользователя",
        "commands.unlock_title": "Разблокировать звание пользователя",
        "commands.set_full_title": "Установить полное звание для пользователя",
        "commands.set_global_average_period": "Установить период глобального среднего",
        # Errors
        "errors.user_not_found": "Пользователь не найден",
        "errors.permission_denied": "❌ Доступ запрещён. Требуются права администратора.",
        "errors.title_locked": "Звание заблокировано и не может быть обновлено автоматически",
        "errors.invalid_percentage": "Неверное значение процента",
        # Messages
        "messages.title_locked": "✅ Звание заблокировано для пользователя",
        "messages.title_unlocked": "✅ Звание разблокировано для пользователя. Автообновление включено.",
        "messages.not_in_table": "Тебя нет в таблице 😢",
        "messages.recheck_complete": "✅ Повторная проверка завершена! Обработано: {count} сообщений",
        # Buttons
        "buttons.my_stats": "📊 Моя статистика",
        "buttons.leaderboard": "👥 Таблица лидеров",
        "buttons.help": "📝 Помощь",
        "buttons.settings": "⚙️ Настройки",
        "buttons.lock_title": "🔒 Заблокировать звание",
        "buttons.back": "⬅️ Назад",
        # Stats
        "stats.global_average": "Глобальное среднее",
        "stats.user_stats": "Статистика пользователя",
        "stats.position": "Позиция",
        "stats.title": "Звание",
        "stats.percentage": "Процент",
        # Admin
        "admin.recheck_complete": "✅ Повторная проверка завершена! Обработано: {processed} сообщений, Обновлено званий: {updated} пользователей",
    },
}


def translate(key: str, language: str = "en") -> str:
    """
    Translate key to language with fallback to English.
    
    Args:
        key: Translation key (dot notation: category.key)
        language: Language code ('en' or 'ru')
        
    Returns:
        Translated string or key if not found
    """
    translations = TRANSLATIONS.get(language, TRANSLATIONS["en"])
    return translations.get(key, TRANSLATIONS["en"].get(key, key))


def format_translated_message(key: str, language: str = "en", **kwargs) -> str:
    """
    Translate key and format with placeholders.
    
    Args:
        key: Translation key
        language: Language code
        **kwargs: Format placeholders
        
    Returns:
        Formatted translated string
    """
    message = translate(key, language)
    try:
        return message.format(**kwargs)
    except KeyError:
        return message
