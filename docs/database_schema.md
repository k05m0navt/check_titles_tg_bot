# Database Schema Documentation

## Overview

This document describes the database schema for the Telegram Bot application using Supabase (PostgreSQL).

## Tables

### 1. users

Main user data table storing Telegram user information and title management.

**Fields:**
- `id` (SERIAL PRIMARY KEY): Internal user ID
- `telegram_user_id` (BIGINT UNIQUE NOT NULL): Telegram user ID (primary identifier, persistent)
- `telegram_username` (VARCHAR(255)): Telegram username (nullable, can change)
- `display_name` (VARCHAR(255)): Display name
- `full_title` (TEXT NOT NULL DEFAULT ''): Full/base title set by admin (e.g., "Super Gay Title")
- `title` (TEXT NOT NULL DEFAULT ''): Displayed title calculated as substring of full_title based on percentage rules
- `title_letter_count` (INTEGER NOT NULL DEFAULT 0): Cached letter count for sorting performance
- `title_locked` (BOOLEAN NOT NULL DEFAULT FALSE): Flag to prevent automatic title updates
- `timezone` (VARCHAR(50) NOT NULL DEFAULT 'UTC'): User's timezone preference
- `language` (VARCHAR(10) NOT NULL DEFAULT 'en'): User's language preference ('en' or 'ru')
- `last_percentage` (INTEGER): Last processed percentage value
- `last_processed_date` (DATE): Last date when a percentage message was processed (timezone-aware)
- `migration_batch_id` (VARCHAR(50)): Migration batch identifier for rollback support (nullable)
- `migration_timestamp` (TIMESTAMP WITH TIME ZONE): Migration timestamp for rollback support (nullable)
- `created_at` (TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()): Record creation timestamp
- `updated_at` (TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()): Record update timestamp

**Indexes:**
- `idx_users_telegram_user_id` (UNIQUE): Fast lookup by Telegram user ID
- `idx_users_telegram_username`: Username lookup (partial index, only non-null values)
- `idx_users_title_letter_count`: Leaderboard sorting performance
- `idx_users_migration_batch`: Migration rollback queries (partial index, only non-null values)

**Performance Rationale:**
- `telegram_user_id` is the primary lookup key for all user operations
- `title_letter_count` is cached to avoid expensive letter counting on every leaderboard query
- Username index is partial (WHERE NOT NULL) since usernames can be null

**Active User Definition:**
Active users = all users in database (any user who has used the bot at least once). Counted via `COUNT(*)` from `users` table.

### 2. daily_snapshots

Daily statistics snapshots for batch calculation of trends and statistics.

**Fields:**
- `id` (SERIAL PRIMARY KEY): Internal snapshot ID
- `user_id` (INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE): Foreign key to users
- `snapshot_date` (DATE NOT NULL): Date of the snapshot
- `percentage` (INTEGER): Percentage value at snapshot time
- `title` (TEXT NOT NULL): Title at snapshot time
- `title_letter_count` (INTEGER NOT NULL): Letter count at snapshot time
- `created_at` (TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()): Record creation timestamp
- UNIQUE constraint on (user_id, snapshot_date): Ensures one snapshot per user per day

**Indexes:**
- `idx_daily_snapshots_user_date` (UNIQUE): Fast lookup of user's snapshots by date
- `idx_daily_snapshots_date`: Period-based statistics queries (e.g., last 30 days)

**Performance Rationale:**
- UNIQUE constraint prevents duplicate snapshots and enables idempotent job execution
- Date index enables efficient filtering for period-based statistics (daily/weekly/monthly trends)
- Cascading delete ensures snapshots are removed when user is deleted

**Activity Definition:**
Snapshots are created only for users where `last_processed_date` equals the snapshot date (users who received a percentage message that day and had their title updated). If no users had activity on a given date, no snapshots are created (expected behavior, not an error).

### 3. title_history

Complete history of all title changes for statistics and audit purposes.

**Fields:**
- `id` (SERIAL PRIMARY KEY): Internal history ID
- `user_id` (INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE): Foreign key to users
- `old_title` (TEXT): Previous title (NULL for initial creation)
- `new_title` (TEXT NOT NULL): New title
- `percentage` (INTEGER): Percentage value that triggered the change (if applicable)
- `change_type` (VARCHAR(50) NOT NULL): Type of change ('created', 'automatic', 'manual_admin')
- `created_at` (TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()): Change timestamp

**Indexes:**
- `idx_title_history_user_id`: Fast lookup of user's title history (sorted by date DESC)

**Performance Rationale:**
- Index enables efficient retrieval of recent title changes for user statistics
- Cascading delete ensures history is removed when user is deleted

**Change Types:**
- `created`: Initial title creation when user is first created
- `automatic`: Automatic title update based on percentage rules
- `manual_admin`: Manual title change by admin (even if title is locked)

### 4. bot_settings

Global bot configuration settings.

**Fields:**
- `id` (SERIAL PRIMARY KEY): Internal settings ID
- `key` (VARCHAR(100) UNIQUE NOT NULL): Setting key (e.g., 'global_average_period_days')
- `value` (TEXT NOT NULL): Setting value (stored as text, parsed as needed)
- `description` (TEXT): Human-readable description of the setting
- `created_at` (TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()): Record creation timestamp
- `updated_at` (TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()): Record update timestamp

**Initial Settings:**
- `global_average_period_days`: '0' (0 = all-time, or custom period in days)
- `admin_user_id`: '' (optional, can be set via env var)

### 5. statistics_cache

Cached statistics calculations for performance optimization.

**Fields:**
- `id` (SERIAL PRIMARY KEY): Internal cache ID
- `calculation_type` (VARCHAR(100) NOT NULL): Type of calculation (e.g., 'global_average')
- `period_days` (INTEGER NOT NULL): Period for calculation (0 = all-time)
- `calculated_value` (NUMERIC(10, 2) NOT NULL): Cached calculated value
- `expires_at` (TIMESTAMP WITH TIME ZONE NOT NULL): Cache expiration timestamp
- `created_at` (TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()): Cache creation timestamp
- UNIQUE constraint on (calculation_type, period_days): One cache entry per calculation type/period

**Indexes:**
- `idx_statistics_cache_expires`: Cache cleanup job queries (delete expired entries)
- `idx_statistics_cache_lookup` (UNIQUE): Fast cache lookup by type and period

**Performance Rationale:**
- Cache prevents expensive recalculations on every statistics request
- Expiration mechanism ensures cache freshness
- UNIQUE constraint ensures one cache entry per calculation type/period

**Cache Invalidation:**
When daily snapshots are created, related cache entries are invalidated (deleted) to prevent stale statistics.

## Relationships

```
users (1) ──< (N) daily_snapshots
users (1) ──< (N) title_history
```

## Index Usage

| Query Type | Index Used | Performance Impact |
|------------|------------|-------------------|
| User lookup by telegram_user_id | idx_users_telegram_user_id | O(1) - UNIQUE index |
| User lookup by username | idx_users_telegram_username | O(log n) - partial index |
| Leaderboard sorting | idx_users_title_letter_count | O(n log n) → O(n) with index |
| Daily snapshots by user | idx_daily_snapshots_user_date | O(log n) - UNIQUE index |
| Period-based statistics | idx_daily_snapshots_date | O(log n) - enables range queries |
| Title history retrieval | idx_title_history_user_id | O(log n) - sorted by date DESC |
| Cache lookup | idx_statistics_cache_lookup | O(1) - UNIQUE index |
| Cache cleanup | idx_statistics_cache_expires | O(log n) - enables range deletion |

## Constraints

- **Foreign Keys:** All foreign keys use `ON DELETE CASCADE` to ensure data consistency
- **Unique Constraints:** 
  - `users.telegram_user_id` (prevent duplicate users)
  - `daily_snapshots(user_id, snapshot_date)` (prevent duplicate snapshots)
  - `bot_settings.key` (prevent duplicate settings)
  - `statistics_cache(calculation_type, period_days)` (prevent duplicate cache entries)

## Triggers

- `update_users_updated_at`: Automatically updates `updated_at` timestamp on user updates
- `update_bot_settings_updated_at`: Automatically updates `updated_at` timestamp on settings updates
