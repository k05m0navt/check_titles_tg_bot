#!/usr/bin/env python3
"""Clean up all migrations and reset the database.

This script drops all tables created by migrations and clears the migration tracking,
allowing you to rerun migrations from scratch.
"""

import asyncio
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote_plus, urlparse, urlunparse

try:
    import asyncpg
except ImportError:
    print("❌ asyncpg is required!")
    print("   Install it with: pip install asyncpg")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not found, skipping .env file loading")


def normalize_database_url(url: str) -> str:
    """Normalize database URL by properly encoding password with special characters."""
    try:
        # Check if URL might have unencoded special characters in password
        password_pattern = r"postgresql://([^:]+):([^@]+)@"
        match = re.match(password_pattern, url)
        
        if match:
            username = match.group(1)
            password = match.group(2)
            rest_of_url = url[match.end():]  # Everything after @
            
            # Check if password contains special characters that need encoding
            needs_encoding = any(char in password for char in ['#', '@', '%', '&', '=', '?', '/', ':', ' '])
            
            if needs_encoding:
                # URL-encode the password
                encoded_password = quote_plus(password)
                # Reconstruct URL with encoded password
                normalized = f"postgresql://{username}:{encoded_password}@{rest_of_url}"
                return normalized
        
        # Try standard parsing for already-encoded or simple passwords
        parsed = urlparse(url)
        if parsed.username and parsed.password:
            encoded_password = quote_plus(parsed.password)
            netloc = f"{parsed.username}:{encoded_password}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            
            normalized = urlunparse((
                parsed.scheme,
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            return normalized
        
        return url
    except Exception as e:
        print(f"⚠️  Warning: Could not parse DATABASE_URL, using as-is: {str(e)}")
        return url


def get_database_url() -> str:
    """Get database URL from environment variables."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        database_url = database_url.strip('"').strip("'")
        return normalize_database_url(database_url)
    
    print("❌ DATABASE_URL not found in environment variables!")
    sys.exit(1)


async def clean_migrations():
    """Drop all tables and clear migration tracking."""
    print("🧹 Cleaning up migrations...\n")
    
    database_url = get_database_url()
    
    # Mask password in debug output
    debug_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', database_url)
    print(f"🔗 Connecting to: {debug_url}")
    
    try:
        # Disable statement cache for PgBouncer compatibility
        # PgBouncer Transaction/Statement mode doesn't support prepared statements
        conn = await asyncpg.connect(
            database_url,
            statement_cache_size=0  # Disable prepared statements for PgBouncer
        )
        print("✓ Connected to database\n")
    except Exception as e:
        print(f"❌ Failed to connect to database: {str(e)}")
        return
    
    try:
        # List of tables to drop (in reverse dependency order - child tables first)
        # Using CASCADE to automatically drop dependent objects (foreign keys, triggers, etc.)
        tables_to_drop = [
            "daily_snapshots",      # References users
            "title_history",        # References users
            "statistics_cache",
            "bot_settings",         # Has triggers
            "users",                # Parent table with triggers
            "schema_migrations",    # Migration tracking table (drop last)
        ]
        
        print("📋 Dropping tables (with CASCADE to handle dependencies)...")
        dropped_tables = []
        skipped_tables = []
        
        async with conn.transaction():
            for table in tables_to_drop:
                try:
                    # Check if table exists
                    exists = await conn.fetchval("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = $1
                        )
                    """, table)
                    
                    if exists:
                        # Drop table with CASCADE to handle foreign keys, triggers, etc.
                        await conn.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
                        dropped_tables.append(table)
                        print(f"  ✓ Dropped table: {table}")
                    else:
                        skipped_tables.append(table)
                        print(f"  ⏭️  Table doesn't exist: {table}")
                        
                except Exception as e:
                    print(f"  ❌ Error dropping table {table}: {str(e)}")
            
            # Drop functions if they still exist (might have been dropped by CASCADE)
            print("\n📋 Dropping functions...")
            functions_to_drop = [
                "update_updated_at_column",
            ]
            
            for func in functions_to_drop:
                try:
                    exists = await conn.fetchval("""
                        SELECT EXISTS (
                            SELECT FROM pg_proc 
                            JOIN pg_namespace ON pg_proc.pronamespace = pg_namespace.oid
                            WHERE pg_namespace.nspname = 'public'
                            AND proname = $1
                        )
                    """, func)
                    
                    if exists:
                        await conn.execute(f'DROP FUNCTION IF EXISTS "{func}()" CASCADE')
                        print(f"  ✓ Dropped function: {func}")
                    else:
                        print(f"  ⏭️  Function doesn't exist: {func} (may have been dropped by CASCADE)")
                        
                except Exception as e:
                    print(f"  ❌ Error dropping function {func}: {str(e)}")
        
        print("\n" + "=" * 60)
        print("✅ Cleanup completed!")
        print(f"   Dropped tables: {len(dropped_tables)}")
        print(f"   Skipped (didn't exist): {len(skipped_tables)}")
        print("=" * 60)
        print("\n💡 You can now run migrations again:")
        print("   pipenv run python scripts/run_migrations.py")
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {str(e)}")
    finally:
        await conn.close()
        print("\n✓ Database connection closed")


async def main():
    """Main entry point."""
    # Confirm before proceeding
    print("⚠️  WARNING: This will drop all tables created by migrations!")
    print("   This action cannot be undone.\n")
    
    confirm = input("Type 'yes' to continue, or anything else to cancel: ")
    if confirm.lower() != 'yes':
        print("❌ Cancelled. No changes made.")
        return
    
    await clean_migrations()


if __name__ == "__main__":
    asyncio.run(main())
