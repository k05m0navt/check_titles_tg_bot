"""Google Sheets to Supabase migration script."""

import argparse
import asyncio
import json
import csv
import uuid
from datetime import datetime
from typing import List, Dict, Any
import gspread
from dotenv import load_dotenv
import os

from src.infrastructure.config.settings import settings
from src.infrastructure.database.supabase_client import get_supabase_client
from src.infrastructure.database.repositories.supabase_user_repository import SupabaseUserRepository
from src.domain.value_objects.title import Title

load_dotenv()


class MigrationScript:
    """Migration script for Google Sheets to Supabase."""

    def __init__(self):
        """Initialize migration script."""
        self.user_repository = SupabaseUserRepository()
        self.migration_batch_id = str(uuid.uuid4())
        self.migration_timestamp = datetime.now()

    async def dry_run(self, csv_path: str) -> None:
        """Preview migration without executing."""
        print(f"🔍 DRY RUN MODE - Migration Batch ID: {self.migration_batch_id}")
        print("=" * 60)

        rows = self._load_csv(csv_path)
        print(f"📊 Found {len(rows)} rows to migrate\n")

        for i, row in enumerate(rows[:10], 1):  # Preview first 10
            print(f"{i}. {row.get('name', 'N/A')} (@{row.get('tg_name', 'N/A')})")
            print(f"   Title: {row.get('title', 'N/A')}")
            print(f"   Letters: {row.get('letters', 'N/A')}\n")

        if len(rows) > 10:
            print(f"... and {len(rows) - 10} more rows\n")

        print("✅ Dry run complete - no changes made")
        print(f"To execute migration, use: --execute {csv_path}")

    async def execute(self, csv_path: str) -> None:
        """Execute migration."""
        print(f"🚀 EXECUTING MIGRATION - Batch ID: {self.migration_batch_id}")
        print("=" * 60)

        rows = self._load_csv(csv_path)
        print(f"📊 Migrating {len(rows)} rows...\n")

        successful = 0
        skipped = 0
        errors = []

        for row in rows:
            try:
                # Note: Would need Telegram API to resolve username to user_id
                # For now, skip username resolution
                print(f"⚠️  Skipping {row.get('name')} - username resolution not implemented")
                skipped += 1
                errors.append(f"{row.get('name')}: Username resolution not implemented")
            except Exception as e:
                print(f"❌ Error migrating {row.get('name')}: {str(e)}")
                errors.append(f"{row.get('name')}: {str(e)}")

        print("\n" + "=" * 60)
        print(f"✅ Migration complete!")
        print(f"   Successful: {successful}")
        print(f"   Skipped: {skipped}")
        print(f"   Errors: {len(errors)}")

        if errors:
            print("\nErrors:")
            for error in errors[:10]:
                print(f"  - {error}")

    async def rollback(self, batch_id: str) -> None:
        """Rollback migration by batch_id."""
        print(f"⏪ ROLLBACK MODE - Batch ID: {batch_id}")
        print("=" * 60)
        print("⚠️  Rollback not fully implemented - manual database intervention required")
        print(f"To rollback, delete users where migration_batch_id = '{batch_id}'")

    def _load_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """Load CSV file."""
        rows = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        return rows


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate Google Sheets to Supabase")
    parser.add_argument("--dry-run", type=str, help="CSV file path for dry run")
    parser.add_argument("--execute", type=str, help="CSV file path for execution")
    parser.add_argument("--rollback", type=str, help="Batch ID for rollback")

    args = parser.parse_args()

    script = MigrationScript()

    if args.dry_run:
        await script.dry_run(args.dry_run)
    elif args.execute:
        confirm = input("⚠️  This will modify the database. Continue? (yes/no): ")
        if confirm.lower() == "yes":
            await script.execute(args.execute)
        else:
            print("❌ Migration cancelled")
    elif args.rollback:
        confirm = input("⚠️  This will delete migrated data. Continue? (yes/no): ")
        if confirm.lower() == "yes":
            await script.rollback(args.rollback)
        else:
            print("❌ Rollback cancelled")
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
