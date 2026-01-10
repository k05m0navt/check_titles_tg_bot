-- Migration: 001_initial_schema.sql
-- Description: Create initial database schema with all tables, indexes, and constraints
-- Tables: users, daily_snapshots, title_history, bot_settings, statistics_cache

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT UNIQUE NOT NULL,
    telegram_username VARCHAR(255),
    display_name VARCHAR(255),
    title TEXT NOT NULL DEFAULT '',
    title_letter_count INTEGER NOT NULL DEFAULT 0,
    title_locked BOOLEAN NOT NULL DEFAULT FALSE,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    last_percentage INTEGER,
    last_processed_date DATE,
    migration_batch_id VARCHAR(50),
    migration_timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Critical indexes for users table
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_user_id ON users(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_users_telegram_username ON users(telegram_username) WHERE telegram_username IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_title_letter_count ON users(title_letter_count);
CREATE INDEX IF NOT EXISTS idx_users_migration_batch ON users(migration_batch_id) WHERE migration_batch_id IS NOT NULL;

-- Daily snapshots table
CREATE TABLE IF NOT EXISTS daily_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    percentage INTEGER,
    title TEXT NOT NULL,
    title_letter_count INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, snapshot_date)
);

-- Critical indexes for daily_snapshots table
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_snapshots_user_date ON daily_snapshots(user_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_snapshots_date ON daily_snapshots(snapshot_date DESC);

-- Title history table
CREATE TABLE IF NOT EXISTS title_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    old_title TEXT,
    new_title TEXT NOT NULL,
    percentage INTEGER,
    change_type VARCHAR(50) NOT NULL, -- 'created', 'automatic', 'manual_admin'
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Critical indexes for title_history table
CREATE INDEX IF NOT EXISTS idx_title_history_user_id ON title_history(user_id, created_at DESC);

-- Bot settings table
CREATE TABLE IF NOT EXISTS bot_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Statistics cache table
CREATE TABLE IF NOT EXISTS statistics_cache (
    id SERIAL PRIMARY KEY,
    calculation_type VARCHAR(100) NOT NULL, -- 'global_average'
    period_days INTEGER NOT NULL, -- 0 = all-time
    calculated_value NUMERIC(10, 2) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(calculation_type, period_days)
);

-- Critical indexes for statistics_cache table
CREATE INDEX IF NOT EXISTS idx_statistics_cache_expires ON statistics_cache(expires_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_statistics_cache_lookup ON statistics_cache(calculation_type, period_days);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at for users
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-update updated_at for bot_settings
CREATE TRIGGER update_bot_settings_updated_at BEFORE UPDATE ON bot_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
