"""Supabase implementation of statistics repository."""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import date, datetime

from src.infrastructure.database.supabase_client import get_supabase_client
from ....domain.repositories.statistics_repository import IStatisticsRepository


class SupabaseStatisticsRepository(IStatisticsRepository):
    """Supabase implementation of statistics repository."""

    async def create_daily_snapshot(
        self,
        user_id: int,
        snapshot_date: date,
        percentage: Optional[int],
        title: str,
        title_letter_count: int,
    ) -> None:
        """Create daily snapshot for user (idempotent)."""
        client = await get_supabase_client()
        
        def _insert():
            # Use upsert to handle idempotency (UNIQUE constraint on user_id, snapshot_date)
            response = (
                client.table("daily_snapshots")
                .upsert(
                    {
                        "user_id": user_id,
                        "snapshot_date": snapshot_date.isoformat(),
                        "percentage": percentage,
                        "title": title,
                        "title_letter_count": title_letter_count,
                    },
                    on_conflict="user_id,snapshot_date",
                )
                .execute()
            )
            return response.data
        
        await asyncio.to_thread(_insert)

    async def get_snapshots_by_period(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get snapshots for period (optionally filtered by user)."""
        client = await get_supabase_client()
        
        def _query():
            query = (
                client.table("daily_snapshots")
                .select("*")
                .gte("snapshot_date", start_date.isoformat())
                .lte("snapshot_date", end_date.isoformat())
            )
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            query = query.order("snapshot_date", desc=True)
            response = query.execute()
            return response.data
        
        data = await asyncio.to_thread(_query)
        return data or []

    async def get_global_average(
        self, period_days: int = 0
    ) -> Optional[float]:
        """Get global average percentage for period (0 = all-time)."""
        client = await get_supabase_client()
        
        def _calculate():
            query = client.table("daily_snapshots").select("percentage")
            
            if period_days > 0:
                # Calculate start date
                from datetime import timedelta
                end_date = date.today()
                start_date = end_date - timedelta(days=period_days)
                query = (
                    query.gte("snapshot_date", start_date.isoformat())
                    .lte("snapshot_date", end_date.isoformat())
                )
            
            # Filter out NULL percentages
            query = query.not_.is_("percentage", "null")
            response = query.execute()
            
            if not response.data:
                return None
            
            percentages = [row["percentage"] for row in response.data if row.get("percentage") is not None]
            if not percentages:
                return None
            
            return sum(percentages) / len(percentages)
        
        return await asyncio.to_thread(_calculate)

    async def cache_statistics(
        self,
        calculation_type: str,
        period_days: int,
        value: float,
        expires_at: datetime,
    ) -> None:
        """Cache statistics calculation."""
        client = await get_supabase_client()
        
        def _upsert():
            response = (
                client.table("statistics_cache")
                .upsert(
                    {
                        "calculation_type": calculation_type,
                        "period_days": period_days,
                        "calculated_value": float(value),
                        "expires_at": expires_at.isoformat(),
                    },
                    on_conflict="calculation_type,period_days",
                )
                .execute()
            )
            return response.data
        
        await asyncio.to_thread(_upsert)

    async def get_cached_statistics(
        self, calculation_type: str, period_days: int
    ) -> Optional[float]:
        """Get cached statistics if valid."""
        client = await get_supabase_client()
        
        def _query():
            response = (
                client.table("statistics_cache")
                .select("*")
                .eq("calculation_type", calculation_type)
                .eq("period_days", period_days)
                .execute()
            )
            return response.data[0] if response.data else None
        
        cache_entry = await asyncio.to_thread(_query)
        if not cache_entry:
            return None
        
        # Check if cache is expired
        expires_at = datetime.fromisoformat(cache_entry["expires_at"])
        if datetime.now() >= expires_at:
            return None
        
        return float(cache_entry["calculated_value"])

    async def is_cache_valid(
        self, calculation_type: str, period_days: int
    ) -> bool:
        """Check if cache entry exists and is not expired."""
        cached_value = await self.get_cached_statistics(calculation_type, period_days)
        return cached_value is not None

    async def invalidate_cache(
        self, calculation_type: str, period_days: Optional[int] = None
    ) -> None:
        """Invalidate cache entries (delete expired or specific entries)."""
        client = await get_supabase_client()
        
        def _delete():
            query = client.table("statistics_cache").delete()
            query = query.eq("calculation_type", calculation_type)
            
            if period_days is not None:
                query = query.eq("period_days", period_days)
            
            response = query.execute()
            return response.data
        
        await asyncio.to_thread(_delete)
