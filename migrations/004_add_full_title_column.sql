-- Migration: 004_add_full_title_column.sql
-- Description: Add full_title column to users table for new title management strategy
-- Date: 2026-01-10

-- Add full_title column to users table
-- full_title is the base title set by admin, displayed title is calculated from it
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS full_title TEXT NOT NULL DEFAULT '';

-- Update existing users: set full_title to current title (if title exists)
-- This ensures existing data is preserved during migration
UPDATE users 
SET full_title = title 
WHERE full_title = '' AND title != '';

-- Add comment to document the column purpose
COMMENT ON COLUMN users.full_title IS 'Full/base title set by admin. Displayed title is calculated as substring of full_title based on percentage rules.';
