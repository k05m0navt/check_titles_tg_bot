-- Migration: 005_add_default_title_setting.sql
-- Description: Add default_title setting to bot_settings table
-- Date: 2026-01-10

-- Insert default_title setting with empty string as default value
INSERT INTO bot_settings (key, value, description)
VALUES 
    ('default_title', '', 'Default/base title for all new users. Admin sets this, all new registrations get this as full_title.')
ON CONFLICT (key) DO NOTHING;
