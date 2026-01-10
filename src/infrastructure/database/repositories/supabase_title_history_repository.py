"""Supabase implementation of title history repository."""

import asyncio
from typing import List, Optional, Dict, Any

from src.infrastructure.database.supabase_client import get_supabase_client
from ....domain.repositories.title_history_repository import ITitleHistoryRepository


class SupabaseTitleHistoryRepository(ITitleHistoryRepository):
    """Supabase implementation of title history repository."""

    async def save(
        self,
        user_id: int,
        old_title: Optional[str],
        new_title: str,
        percentage: Optional[int],
        change_type: str,
    ) -> None:
        """Save title history entry."""
        client = await get_supabase_client()
        
        def _insert():
            response = (
                client.table("title_history")
                .insert(
                    {
                        "user_id": user_id,
                        "old_title": old_title,
                        "new_title": new_title,
                        "percentage": percentage,
                        "change_type": change_type,
                    }
                )
                .execute()
            )
            return response.data
        
        await asyncio.to_thread(_insert)

    async def get_by_user(
        self, user_id: int, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get title history for user (most recent first)."""
        client = await get_supabase_client()
        
        def _query():
            query = (
                client.table("title_history")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
            )
            if limit:
                query = query.limit(limit)
            response = query.execute()
            return response.data
        
        data = await asyncio.to_thread(_query)
        return data or []

    async def get_recent(
        self, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent title changes across all users."""
        client = await get_supabase_client()
        
        def _query():
            response = (
                client.table("title_history")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        
        data = await asyncio.to_thread(_query)
        return data or []
