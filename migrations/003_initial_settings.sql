-- Migration: 003_initial_settings.sql
-- Description: Insert initial bot settings

INSERT INTO bot_settings (key, value, description)
VALUES 
    ('global_average_period_days', '0', 'Period for global average calculation in days (0 = all-time)'),
    ('admin_user_id', '', 'Admin Telegram user ID (optional, can be set via env var)')
ON CONFLICT (key) DO NOTHING;
