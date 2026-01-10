"""Supabase implementation of user repository."""

import asyncio
from typing import List, Optional
from datetime import date, datetime

from src.infrastructure.database.supabase_client import get_supabase_client
from ....domain.entities.user import User
from ....domain.repositories.user_repository import IUserRepository
from ....domain.value_objects.title import Title
from ....domain.value_objects.percentage import Percentage
from ....domain.value_objects.timezone import Timezone
from ....domain.exceptions import UserNotFoundError


class SupabaseUserRepository(IUserRepository):
    """Supabase implementation of user repository."""

    async def get_by_telegram_id(self, telegram_user_id: int) -> Optional[User]:
        """Get user by Telegram user ID."""
        client = await get_supabase_client()
        
        def _query():
            response = (
                client.table("users")
                .select("*")
                .eq("telegram_user_id", telegram_user_id)
                .execute()
            )
            return response.data[0] if response.data else None
        
        data = await asyncio.to_thread(_query)
        if not data:
            return None
        return self._to_user(data)

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by Telegram username."""
        client = await get_supabase_client()
        
        def _query():
            response = (
                client.table("users")
                .select("*")
                .eq("telegram_username", username)
                .execute()
            )
            return response.data[0] if response.data else None
        
        data = await asyncio.to_thread(_query)
        if not data:
            return None
        return self._to_user(data)

    async def save(self, user: User) -> User:
        """Save or update user."""
        client = await get_supabase_client()
        user_dict = self._to_dict(user)
        
        def _upsert():
            # Use upsert to handle both insert and update
            response = (
                client.table("users")
                .upsert(user_dict, on_conflict="telegram_user_id")
                .execute()
            )
            return response.data[0] if response.data else user_dict
        
        data = await asyncio.to_thread(_upsert)
        return self._to_user(data)

    async def find_all(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> List[User]:
        """Find all users with pagination."""
        client = await get_supabase_client()
        
        def _query():
            query = client.table("users").select("*")
            if limit:
                query = query.limit(limit).offset(offset)
            response = query.execute()
            return response.data
        
        data_list = await asyncio.to_thread(_query)
        return [self._to_user(data) for data in data_list]

    async def find_by_title_letter_count_range(
        self,
        min_count: Optional[int] = None,
        max_count: Optional[int] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        sort_order: str = "asc",
    ) -> List[User]:
        """Find users by title letter count range with sorting."""
        client = await get_supabase_client()
        
        def _query():
            query = client.table("users").select("*")
            
            if min_count is not None:
                query = query.gte("title_letter_count", min_count)
            if max_count is not None:
                query = query.lte("title_letter_count", max_count)
            
            # Sort by title_letter_count
            order_desc = sort_order.lower() == "desc"
            query = query.order("title_letter_count", desc=order_desc)
            
            if limit:
                query = query.limit(limit).offset(offset)
            
            response = query.execute()
            return response.data
        
        data_list = await asyncio.to_thread(_query)
        return [self._to_user(data) for data in data_list]

    async def count_active_users(self) -> int:
        """
        Count active users (all users in database).
        
        Note: Active users = all users who have used the bot at least once.
        For 100% rule, this count is always queried fresh (never cached).
        """
        client = await get_supabase_client()
        
        def _count():
            # Use SELECT COUNT(*) for atomic operation
            # Note: supabase-py doesn't have direct COUNT, so we select all and count
            # For better performance in production, use a database function or raw SQL
            response = client.table("users").select("id", count="exact").execute()
            return response.count if hasattr(response, "count") else len(response.data)
        
        count = await asyncio.to_thread(_count)
        return count or 0

    async def delete(self, telegram_user_id: int) -> bool:
        """
        Delete user by Telegram user ID.
        
        Args:
            telegram_user_id: Telegram user ID of user to delete
            
        Returns:
            True if user was deleted, False if user not found
            
        Note:
            Due to ON DELETE CASCADE in database schema, related records
            (snapshots, title_history) will be automatically deleted.
        """
        client = await get_supabase_client()
        
        def _delete():
            # Delete user (cascade will handle related records)
            # Supabase returns deleted rows in response.data
            response = (
                client.table("users")
                .delete()
                .eq("telegram_user_id", telegram_user_id)
                .execute()
            )
            # Check if any rows were actually deleted
            return len(response.data) > 0 if response.data else False
        
        deleted = await asyncio.to_thread(_delete)
        return deleted

    def _to_user(self, data: dict) -> User:
        """Convert database row to User entity."""
        return User(
            id=data.get("id"),
            telegram_user_id=data["telegram_user_id"],
            telegram_username=data.get("telegram_username"),
            display_name=data.get("display_name"),
            full_title=Title(data.get("full_title", "")),
            title=Title(data.get("title", "")),
            title_letter_count=data.get("title_letter_count", 0),
            title_locked=data.get("title_locked", False),
            timezone=Timezone.from_string(data.get("timezone", "UTC")),
            language=data.get("language", "en"),
            last_percentage=Percentage.from_optional(data.get("last_percentage")),
            last_processed_date=(
                date.fromisoformat(data["last_processed_date"])
                if data.get("last_processed_date")
                else None
            ),
            migration_batch_id=data.get("migration_batch_id"),
            migration_timestamp=(
                datetime.fromisoformat(data["migration_timestamp"])
                if data.get("migration_timestamp")
                else None
            ),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else None
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if data.get("updated_at")
                else None
            ),
        )

    def _to_dict(self, user: User) -> dict:
        """Convert User entity to database row dictionary."""
        user_dict = {
            "telegram_user_id": user.telegram_user_id,
            "telegram_username": user.telegram_username,
            "display_name": user.display_name,
            "full_title": str(user.full_title),
            "title": str(user.title),
            "title_letter_count": user.title_letter_count,
            "title_locked": user.title_locked,
            "timezone": str(user.timezone),
            "language": user.language,
            "last_percentage": int(user.last_percentage) if user.last_percentage else None,
            "last_processed_date": (
                user.last_processed_date.isoformat()
                if user.last_processed_date
                else None
            ),
            "migration_batch_id": user.migration_batch_id,
            "migration_timestamp": (
                user.migration_timestamp.isoformat()
                if user.migration_timestamp
                else None
            ),
        }
        # Only include id if it has a value (for updates)
        # For new users (id=None), exclude it to let database auto-generate
        if user.id is not None:
            user_dict["id"] = user.id
        return user_dict