"""Inline keyboard builder for Telegram bot."""

from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ...infrastructure.i18n.translations import translate


class InlineKeyboardBuilder:
    """Builder for inline keyboards."""

    @staticmethod
    def build_main_keyboard(
        is_admin: bool = False, language: str = "en"
    ) -> InlineKeyboardMarkup:
        """
        Build main inline keyboard with buttons.
        
        Args:
            is_admin: Whether user is admin (shows admin buttons)
            language: Language code for button labels
            
        Returns:
            InlineKeyboardMarkup with buttons
        """
        buttons: List[List[InlineKeyboardButton]] = [
            [
                InlineKeyboardButton(
                    translate("buttons.my_stats", language),
                    callback_data="me"
                )
            ],
            [
                InlineKeyboardButton(
                    translate("buttons.leaderboard", language),
                    callback_data="leaderboard"
                )
            ],
            [
                InlineKeyboardButton(
                    translate("buttons.help", language),
                    callback_data="help"
                )
            ],
        ]

        if is_admin:
            buttons.append(
                [
                    InlineKeyboardButton(
                        translate("buttons.settings", language),
                        callback_data="settings"
                    )
                ]
            )
            buttons.append(
                [
                    InlineKeyboardButton(
                        translate("buttons.lock_title", language),
                        callback_data="lock_title"
                    )
                ]
            )

        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def build_back_keyboard(language: str = "en") -> InlineKeyboardMarkup:
        """
        Build keyboard with only a back button.
        
        Args:
            language: Language code for button labels
            
        Returns:
            InlineKeyboardMarkup with back button
        """
        buttons: List[List[InlineKeyboardButton]] = [
            [
                InlineKeyboardButton(
                    translate("buttons.back", language),
                    callback_data="back"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def build_settings_keyboard(language: str = "en") -> InlineKeyboardMarkup:
        """
        Build settings keyboard with back button.
        
        Args:
            language: Language code for button labels
            
        Returns:
            InlineKeyboardMarkup with settings buttons and back button
        """
        # Settings page uses the same back-only keyboard
        return InlineKeyboardBuilder.build_back_keyboard(language)