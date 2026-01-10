#!/usr/bin/env python3
"""Migration runner script for Supabase database.

This script automatically runs SQL migration files in the correct order,
tracks which migrations have been executed, and provides clear feedback.
"""

import asyncio
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime
from urllib.parse import quote_plus, urlparse, urlunparse

try:
    import asyncpg
except ImportError:
    print("❌ asyncpg is required for migrations!")
    print("   Install it with: pip install asyncpg")
    print("   Or using pipenv: pipenv install asyncpg")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not found, skipping .env file loading")
    # Continue without .env file (useful if env vars are set elsewhere)



class MigrationRunner:
    """Handles database migrations with tracking and verification."""

    def __init__(self, database_url: str):
        """Initialize migration runner with database connection string."""
        self.database_url = database_url
        self.migrations_dir = Path(__file__).parent.parent / "migrations"

    async def ensure_migrations_table(self, conn: asyncpg.Connection) -> None:
        """Create migrations tracking table if it doesn't exist."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
        """)
        print("✓ Migrations tracking table ready")

    async def get_applied_migrations(self, conn: asyncpg.Connection) -> List[str]:
        """Get list of already applied migration names."""
        rows = await conn.fetch("SELECT migration_name FROM schema_migrations ORDER BY migration_name")
        return [row["migration_name"] for row in rows]

    def get_migration_files(self) -> List[Tuple[str, Path]]:
        """Get all SQL migration files sorted by name."""
        sql_files = sorted(self.migrations_dir.glob("*.sql"))
        # Filter out migration tracking files if any exist
        migrations = [
            (file.stem, file) for file in sql_files
            if not file.stem.startswith("schema_migrations")
        ]
        return migrations

    def parse_migration_name(self, filename: str) -> str:
        """Extract migration name from filename (e.g., '001_initial_schema' from '001_initial_schema.sql')."""
        return Path(filename).stem

    async def run_migration(self, conn: asyncpg.Connection, migration_name: str, file_path: Path) -> bool:
        """Execute a single migration file.
        
        Uses asyncpg's native support for executing multiple SQL statements.
        For connection poolers (PgBouncer Transaction mode), we execute statements one by one.
        """
        print(f"\n📄 Running migration: {migration_name}...")
        
        try:
            # Read migration file
            sql_content = file_path.read_text(encoding="utf-8")
            
            # Skip empty files
            if not sql_content.strip():
                print(f"  ⚠️  Skipping empty file: {migration_name}")
                return False
            
            # Use regex to handle dollar-quoted strings, then split statements
            # Replace dollar-quoted sections ($$...$$) with placeholders to avoid splitting inside them
            import re as regex_module
            
            # Pattern: $$...$$ (dollar-quoted strings used in PostgreSQL functions)
            dollar_quote_pattern = r'\$\$.*?\$\$'
            dollar_quotes = {}
            placeholder_prefix = "__DOLLAR_QUOTE_"
            placeholder_counter = 0
            
            def replace_dollar_quote(match):
                nonlocal placeholder_counter
                placeholder = f"{placeholder_prefix}{placeholder_counter}__"
                dollar_quotes[placeholder] = match.group(0)
                placeholder_counter += 1
                return placeholder
            
            # Replace all $$...$$ sections with placeholders
            sql_with_placeholders = regex_module.sub(
                dollar_quote_pattern, 
                replace_dollar_quote, 
                sql_content, 
                flags=regex_module.DOTALL
            )
            
            # Remove comments (simple approach - might not handle all edge cases but should work for our migrations)
            lines = []
            in_block_comment = False
            for line in sql_with_placeholders.split('\n'):
                # Handle block comments
                if '/*' in line:
                    parts = line.split('/*')
                    if len(parts) > 1:
                        # Check if comment closes on same line
                        if '*/' in parts[1]:
                            # Comment on same line, remove it
                            comment_start = line.find('/*')
                            comment_end = line.find('*/', comment_start) + 2
                            line = line[:comment_start] + line[comment_end:]
                        else:
                            # Multi-line comment starts
                            in_block_comment = True
                            line = parts[0]
                
                if in_block_comment:
                    if '*/' in line:
                        in_block_comment = False
                        line = line.split('*/', 1)[1]
                    else:
                        continue
                
                # Remove line comments (--), simple approach
                if '--' in line:
                    comment_pos = line.find('--')
                    line = line[:comment_pos].rstrip()
                
                if line.strip():  # Only add non-empty lines
                    lines.append(line)
            
            cleaned_sql = '\n'.join(lines)
            
            # Split by semicolon (which are now safe since dollar quotes are replaced)
            statements = [stmt.strip() for stmt in cleaned_sql.split(';') if stmt.strip()]
            
            # Restore dollar quotes in statements
            for i, statement in enumerate(statements):
                for placeholder, dollar_quote in dollar_quotes.items():
                    statement = statement.replace(placeholder, dollar_quote)
                statements[i] = statement
            
            if not statements:
                print(f"  ⚠️  No SQL statements found in {migration_name}")
                return False
            
            print(f"  📝 Found {len(statements)} SQL statement(s)")
            
            # Execute all statements in a transaction
            # For connection poolers, each statement must be executed separately
            async with conn.transaction():
                for i, statement in enumerate(statements, 1):
                    # Skip empty statements
                    if not statement.strip():
                        continue
                    
                    try:
                        await conn.execute(statement)
                    except Exception as e:
                        # Provide more context about which statement failed
                        print(f"  ❌ Error in statement {i}/{len(statements)}:")
                        print(f"     {str(e)}")
                        # Show first 200 chars of the statement for debugging
                        statement_lines = statement.split('\n')
                        first_line = statement_lines[0][:200] if statement_lines else statement[:200]
                        print(f"     First line: {first_line}...")
                        raise
                
                # Record migration as applied
                await conn.execute(
                    "INSERT INTO schema_migrations (migration_name) VALUES ($1) ON CONFLICT DO NOTHING",
                    migration_name
                )
            
            print(f"  ✓ Migration {migration_name} applied successfully")
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to apply migration {migration_name}: {str(e)}")
            return False

    async def run_all_migrations(self, dry_run: bool = False) -> None:
        """Run all pending migrations."""
        print("🚀 Starting database migrations...\n")
        
        # Get database connection
        try:
            # Debug: show normalized URL (hide password)
            if self.database_url:
                # Mask password in debug output
                debug_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', self.database_url)
                print(f"🔗 Connecting to: {debug_url}")
            
            # Disable statement cache for PgBouncer compatibility
            # PgBouncer Transaction/Statement mode doesn't support prepared statements
            conn = await asyncpg.connect(
                self.database_url,
                statement_cache_size=0  # Disable prepared statements for PgBouncer
            )
            print("✓ Connected to database")
        except asyncpg.InvalidPasswordError as e:
            print(f"❌ Authentication failed: {str(e)}")
            print("\n💡 Check your password in DATABASE_URL")
            print("   Make sure the password is correct and special characters are properly handled")
            return
        except asyncpg.InvalidCatalogNameError as e:
            print(f"❌ Database not found: {str(e)}")
            print("\n💡 Make sure the database name in your connection string is correct")
            return
        except (OSError, asyncpg.PostgresConnectionError) as e:
            error_msg = str(e).lower()
            print(f"❌ Failed to connect to database: {str(e)}")
            
            # Check if it's a DNS resolution error
            if "nodename" in error_msg or "servname" in error_msg or "name or service not known" in error_msg:
                print("\n🔍 DNS Resolution Error Detected")
                print("   The hostname in your DATABASE_URL cannot be resolved.")
                print("\n💡 Solution: Get the EXACT connection string from Supabase Dashboard")
                print("\n   1. Go to your Supabase project dashboard:")
                print("      https://app.supabase.com/project/wmviitultqqdlnsbhdmp")
                print("\n   2. Navigate to: Settings → Database → Connection string")
                print("\n   3. Select the connection mode:")
                print("      - 'Transaction' mode (PgBouncer) - Recommended, port 6543")
                print("      - 'Session' mode (Direct) - Requires IPv6 or IPv4 add-on, port 5432")
                print("\n   4. Click the 'URI' tab (not 'JDBC' or 'Golang')")
                print("\n   5. Copy the ENTIRE connection string exactly as shown")
                print("      Different projects may use different hostname formats!")
                print("\n   6. Replace [PASSWORD] with your actual password")
                print("      If password has #, wrap entire URL in quotes in .env:")
                print('      DATABASE_URL="postgresql://postgres:#M#83bNY63NAGasDXrmp@..."')
                print("\n   ⚠️  Important: Use the EXACT hostname from dashboard - don't guess!")
            else:
                print("\n💡 Make sure you have:")
                print("   1. Set DATABASE_URL in your .env file (wrap in quotes if password has #)")
                print("   2. Got the connection string from Supabase dashboard:")
                print("      Settings → Database → Connection string → URI")
                print("   3. Correct hostname format (check dashboard for exact format)")
            return
        except Exception as e:
            print(f"❌ Unexpected error: {type(e).__name__}: {str(e)}")
            print("\n💡 Check your DATABASE_URL format")
            return
        
        try:
            # Ensure migrations table exists
            await self.ensure_migrations_table(conn)
            
            # Get applied and pending migrations
            applied = await self.get_applied_migrations(conn)
            all_migrations = self.get_migration_files()
            
            # Filter out already applied migrations
            pending_migrations = [
                (name, path) for name, path in all_migrations
                if name not in applied
            ]
            
            if not pending_migrations:
                print("\n✅ All migrations are already applied!")
                print(f"   Applied migrations: {', '.join(applied)}")
                return
            
            print(f"\n📋 Found {len(pending_migrations)} pending migration(s):")
            for name, _ in pending_migrations:
                status = "⏭️  Already applied" if name in applied else "⏳ Pending"
                print(f"   {name}")
            
            if applied:
                print(f"\n📋 Already applied migrations ({len(applied)}):")
                for name in applied:
                    print(f"   ✓ {name}")
            
            if dry_run:
                print("\n🔍 DRY RUN MODE - No changes will be made")
                return
            
            # Run pending migrations
            print(f"\n🔄 Applying {len(pending_migrations)} migration(s)...")
            success_count = 0
            failed_migrations = []
            
            for migration_name, file_path in pending_migrations:
                success = await self.run_migration(conn, migration_name, file_path)
                if success:
                    success_count += 1
                else:
                    failed_migrations.append(migration_name)
            
            # Summary
            print("\n" + "=" * 60)
            if failed_migrations:
                print(f"⚠️  Migration Summary:")
                print(f"   ✓ Successful: {success_count}/{len(pending_migrations)}")
                print(f"   ❌ Failed: {len(failed_migrations)}")
                print(f"   Failed migrations: {', '.join(failed_migrations)}")
            else:
                print(f"✅ All migrations completed successfully!")
                print(f"   Applied {success_count} migration(s)")
            print("=" * 60)
            
        finally:
            await conn.close()
            print("\n✓ Database connection closed")


def normalize_database_url(url: str) -> str:
    """Normalize database URL by properly encoding password with special characters.
    
    Handles passwords with special characters like #, @, %, etc. by URL-encoding them.
    Special handling for passwords with # which urlparse treats as fragment delimiter.
    """
    try:
        # Check if URL might have unencoded special characters in password
        # Pattern: postgresql://user:password@host - password is between : and @
        password_pattern = r"postgresql://([^:]+):([^@]+)@"
        match = re.match(password_pattern, url)
        
        if match:
            username = match.group(1)
            password = match.group(2)
            rest_of_url = url[match.end():]  # Everything after @
            
            # Always encode password to handle special characters properly
            # Special characters that need encoding: #, @, %, &, =, ?, /, :, etc.
            needs_encoding = any(char in password for char in ['#', '@', '%', '&', '=', '?', '/', ':', ' '])
            
            if needs_encoding:
                # URL-encode the password
                encoded_password = quote_plus(password)
                # Reconstruct URL with encoded password
                normalized = f"postgresql://{username}:{encoded_password}@{rest_of_url}"
                return normalized
            else:
                # Even if no special chars, return as-is for consistency
                return url
        
        # Try standard parsing for already-encoded or simple passwords
        parsed = urlparse(url)
        
        if parsed.username and parsed.password:
            # Password was successfully extracted, encode it
            encoded_password = quote_plus(parsed.password)
            
            # Reconstruct netloc with properly encoded password
            netloc = f"{parsed.username}:{encoded_password}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            
            # Reconstruct the full URL
            normalized = urlunparse((
                parsed.scheme,
                netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            return normalized
        elif parsed.username:
            # No password in URL (maybe password was provided separately)
            return url
        else:
            # No authentication info, return as-is
            return url
    except Exception as e:
        # If parsing fails, the URL might be in a different format
        # asyncpg might still handle it, so return original
        print(f"⚠️  Warning: Could not parse DATABASE_URL, using as-is: {str(e)}")
        return url


def get_database_url() -> Optional[str]:
    """Get database URL from environment variables, properly encoding special characters in password."""
    # Option 1: Direct DATABASE_URL (preferred)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Strip quotes if present (python-dotenv might have kept them or not, depending on format)
        database_url = database_url.strip('"').strip("'")
        # Normalize the URL to ensure password is properly encoded
        normalized = normalize_database_url(database_url)
        return normalized
    
    # Option 2: Construct from Supabase URL components
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url and supabase_key:
        # Extract project reference from Supabase URL
        # Example: https://abcdefgh.supabase.co -> abcdefgh
        match = re.search(r"https://([^.]+)\.supabase\.co", supabase_url)
        if match:
            project_ref = match.group(1)
            print("⚠️  DATABASE_URL not found. Using SUPABASE_URL to construct connection string.")
            print("   Note: You'll need to provide your database password.")
            print("\n💡 For better experience, set DATABASE_URL in your .env file:")
            print("   Get it from: Supabase Dashboard → Settings → Database → Connection string → URI")
            print("\n   Format: postgresql://postgres:[YOUR-PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres")
            print("   ⚠️  Important: If your password contains special characters (#, @, %, etc.),")
            print("      you MUST use DATABASE_URL in .env file instead (password will be auto-encoded)")
            
            # Try to get password from env or prompt
            db_password = os.getenv("DATABASE_PASSWORD")
            if not db_password:
                db_password = input("\nEnter your Supabase database password (or set DATABASE_PASSWORD env var): ")
            
            # URL-encode the password to handle special characters
            encoded_password = quote_plus(db_password)
            return f"postgresql://postgres:{encoded_password}@{project_ref}.supabase.co:5432/postgres"
    
    return None


async def main():
    """Main entry point."""
    import sys
    
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    
    database_url = get_database_url()
    if not database_url:
        print("❌ Database connection string not found!")
        print("\nPlease set one of the following in your .env file:")
        print("  - DATABASE_URL (recommended): Direct PostgreSQL connection string")
        print("  - SUPABASE_URL + SUPABASE_KEY + DATABASE_PASSWORD: Auto-constructed")
        print("\nGet DATABASE_URL from:")
        print("  Supabase Dashboard → Settings → Database → Connection string → URI")
        sys.exit(1)
    
    runner = MigrationRunner(database_url)
    await runner.run_all_migrations(dry_run=dry_run)


if __name__ == "__main__":
    asyncio.run(main())
