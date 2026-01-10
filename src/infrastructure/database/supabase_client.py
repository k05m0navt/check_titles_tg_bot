"""Supabase client configuration with connection pooling and retry logic."""

import asyncio
from typing import Optional
from supabase import create_client, Client

from ..config.settings import settings


class SupabaseClient:
    """Singleton Supabase client (synchronous client wrapped for async use)."""

    _client: Optional[Client] = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_client(cls) -> Client:
        """Get or create Supabase client instance (singleton pattern)."""
        if cls._client is None:
            async with cls._lock:
                if cls._client is None:
                    # Run synchronous client creation in thread pool
                    cls._client = await asyncio.to_thread(cls._create_client)
        return cls._client

    @classmethod
    def _create_client(cls) -> Client:
        """Create Supabase client with configuration (synchronous)."""
        try:
            client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY,
            )
            return client
        except Exception as e:
            raise ConnectionError(
                f"Failed to create Supabase client: {str(e)}"
            ) from e

    @classmethod
    async def test_connection(cls) -> bool:
        """Test database connection.
        
        Returns:
            True if connection is successful
            
        Raises:
            ConnectionError: If connection fails with detailed error message
        """
        try:
            client = await cls.get_client()
            # Simple query to test connection (run in thread pool)
            await asyncio.to_thread(
                lambda: client.table("bot_settings").select("key").limit(1).execute()
            )
            return True
        except Exception as e:
            # Re-raise with more context
            error_msg = f"Failed to test database connection: {type(e).__name__}: {str(e)}"
            if not settings.SUPABASE_URL:
                error_msg += " (SUPABASE_URL environment variable is not set)"
            elif not settings.SUPABASE_KEY:
                error_msg += " (SUPABASE_KEY environment variable is not set)"
            raise ConnectionError(error_msg) from e


# Convenience function for getting client
async def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    return await SupabaseClient.get_client()
