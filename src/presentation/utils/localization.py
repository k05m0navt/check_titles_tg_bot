"""Localization utilities for presentation layer."""

from typing import Optional

from ...domain.repositories.user_repository import IUserRepository
from ...infrastructure.i18n.translations import translate, format_translated_message


async def get_user_language(
    user_repository: IUserRepository, telegram_user_id: int
) -> str:
    """
    Get user's language preference from database.
    
    Args:
        user_repository: User repository interface
        telegram_user_id: Telegram user ID
        
    Returns:
        Language code ('en' or 'ru'), default 'en'
    """
    user = await user_repository.get_by_telegram_id(telegram_user_id)
    if not user:
        return "en"
    return user.language


def get_translated_message(
    user_repository: IUserRepository,
    telegram_user_id: int,
    key: str,
) -> str:
    """
    Get translated message for user (async wrapper).
    
    Note: This is a synchronous wrapper - use get_translated_message_async for async.
    """
    # For sync usage, default to English (async version should be used)
    return translate(key, "en")


async def get_translated_message_async(
    user_repository: IUserRepository,
    telegram_user_id: int,
    key: str,
) -> str:
    """
    Get translated message for user (async version).
    
    Args:
        user_repository: User repository interface
        telegram_user_id: Telegram user ID
        key: Translation key
        
    Returns:
        Translated message in user's language
    """
    language = await get_user_language(user_repository, telegram_user_id)
    return translate(key, language)


async def format_translated_message_async(
    user_repository: IUserRepository,
    telegram_user_id: int,
    key: str,
    **kwargs
) -> str:
    """
    Get formatted translated message for user.
    
    Args:
        user_repository: User repository interface
        telegram_user_id: Telegram user ID
        key: Translation key
        **kwargs: Format placeholders
        
    Returns:
        Formatted translated message in user's language
    """
    language = await get_user_language(user_repository, telegram_user_id)
    return format_translated_message(key, language, **kwargs)
