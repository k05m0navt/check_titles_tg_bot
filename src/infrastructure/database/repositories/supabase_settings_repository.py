"""Supabase implementation of settings repository."""

import asyncio
from typing import Optional, Dict

from src.infrastructure.database.supabase_client import get_supabase_client
from ....domain.repositories.settings_repository import ISettingsRepository


class SupabaseSettingsRepository(ISettingsRepository):
    """Supabase implementation of settings repository."""

    async def get(self, key: str) -> Optional[str]:
        """Get setting value by key."""
        client = await get_supabase_client()
        
        def _query():
            response = (
                client.table("bot_settings")
                .select("value")
                .eq("key", key)
                .execute()
            )
            return response.data[0]["value"] if response.data else None
        
        value = await asyncio.to_thread(_query)
        return value

    async def set(
        self, key: str, value: str, description: Optional[str] = None
    ) -> None:
        """Set setting value."""
        client = await get_supabase_client()
        
        def _upsert():
            data = {"key": key, "value": value}
            if description:
                data["description"] = description
            response = (
                client.table("bot_settings")
                .upsert(data, on_conflict="key")
                .execute()
            )
            return response.data
        
        await asyncio.to_thread(_upsert)

    async def get_global_average_period(self) -> int:
        """Get global average period in days (0 = all-time)."""
        value = await self.get("global_average_period_days")
        if value is None:
            return 0  # Default to all-time
        try:
            return int(value)
        except ValueError:
            return 0

    async def set_global_average_period(self, period_days: int) -> None:
        """Set global average period in days (0 = all-time)."""
        await self.set(
            "global_average_period_days",
            str(period_days),
            "Period for global average calculation in days (0 = all-time)",
        )

    async def get_all(self) -> Dict[str, str]:
        """Get all settings as dictionary."""
        client = await get_supabase_client()
        
        def _query():
            response = client.table("bot_settings").select("key, value").execute()
            return {row["key"]: row["value"] for row in response.data}
        
        settings_dict = await asyncio.to_thread(_query)
        return settings_dict or {}

    async def get_default_title(self) -> str:
        """Get default title from bot_settings (key: 'default_title'). Returns empty string if not set."""
        value = await self.get("default_title")
        return value if value is not None else ""

    async def set_default_title(self, title: str) -> None:
        """Set default title in bot_settings (key: 'default_title'). Validates title before setting."""
        # Validate title: max 500 characters, no control characters
        if len(title) > 500:
            raise ValueError("Title too long (max 500 characters)")
        
        # Check for control characters (excluding newlines and spaces which are allowed)
        control_chars = [chr(i) for i in range(32) if i not in [9, 10, 13]]  # Exclude tab, LF, CR
        if any(char in title for char in control_chars):
            raise ValueError("Title contains invalid characters (control characters not allowed)")
        
        await self.set(
            "default_title",
            title.strip(),
            "Default/base title for all new users. Admin sets this, all new registrations get this as full_title.",
        )
