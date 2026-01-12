# Telegram Bot - Title Management with Message Monitoring

A Clean Architecture Telegram bot that monitors @HowGayBot messages, tracks user percentages, and manages titles based on letter-based rules.

## Features

- **Message Monitoring**: Automatically processes messages from @HowGayBot in group chats
- **Title Management**: Updates user titles based on percentage rules:
  - 0% → Add 3 letters
  - 1-5% → Add 1 letter
  - 95-99% → Remove 1 letter
  - 100% → Remove N letters (where N = active user count)
- **Leaderboard**: Sort users by title letter count
- **Statistics**: Daily/weekly/monthly trends and global averages
- **Admin Commands**: Lock/unlock titles, configure statistics period
- **Multi-language Support**: English and Russian
- **Timezone Support**: Configurable timezone for daily reset logic

## Architecture

This project follows Clean Architecture principles with clear separation of concerns:

```
src/
├── domain/           # Business logic (entities, value objects, services)
├── application/      # Use cases and application services
├── infrastructure/   # External concerns (database, config, jobs)
└── presentation/     # Telegram bot handlers and UI
```

## Setup

### Prerequisites

- Python 3.11.12
- Supabase account and project
- Telegram Bot Token (from @BotFather)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd check_titles_tg_bot
```

2. Install dependencies:

**Using pipenv (Recommended):**
```bash
# Create virtual environment and install dependencies
pipenv install

# Activate the virtual environment
pipenv shell
```

**Or using pip:**
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase API key
- `ADMIN_USER_ID` - Your Telegram user ID (recommended)
- `ADMIN_USERNAME` - Your Telegram username (fallback)
- `DATABASE_URL` - Database connection string for migrations (see below)

4. Run database migrations:

   **Method 1: Automated Migration Script (Recommended - Easiest Way)**

   First, get your database connection string:
   
   1. Go to your Supabase project dashboard: https://app.supabase.com
   2. Navigate to **Settings** → **Database**
   3. Scroll down to **Connection string** section
   4. Choose the appropriate connection mode:
      - **Transaction mode (PgBouncer)** - Recommended: Works without IPv6/IPv4 add-on
        - Port: `6543`
        - Format: `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:6543/postgres`
      - **Session mode** - Direct connection, requires IPv6 or IPv4 add-on
        - Port: `5432`
        - Format: `postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
   5. Copy the **URI** connection string from your dashboard
   6. Replace `[YOUR-PASSWORD]` with your actual database password (found in the same section or reset it if needed)
   7. Add it to your `.env` file as `DATABASE_URL` (wrap in quotes if password has special characters)
   
   **Important Notes:**
   - **If you get "nodename nor servname provided" error**: Your project might require connection pooling (port 6543) instead of direct connection (port 5432)
   - **Password with special characters**: The migration script automatically URL-encodes special characters, so you can use the password as-is
   - **Example**: If your password is `#M#83bNY63NAGasDXrmp`, use it directly:
     ```
     DATABASE_URL="postgresql://postgres:#M#83bNY63NAGasDXrmp@db.your-project.supabase.co:6543/postgres"
     ```
   - The script will automatically encode `#` as `%23` and other special characters as needed

   Then run the automated migration script:

   **Using pipenv:**
   ```bash
   pipenv run python scripts/run_migrations.py
   ```

   **Using pip:**
   ```bash
   python scripts/run_migrations.py
   ```

   The script will:
   - ✅ Automatically detect pending migrations
   - ✅ Run them in the correct order
   - ✅ Track which migrations have been applied (prevents running twice)
   - ✅ Show clear progress and error messages
   - ✅ Provide a summary when complete

   **Dry run mode** (preview without applying):
   ```bash
   python scripts/run_migrations.py --dry-run
   ```

   **Method 2: Manual Migration via Supabase SQL Editor (Alternative)**

   If you prefer to run migrations manually:

   1. Go to your Supabase project dashboard: https://app.supabase.com
   2. Navigate to **SQL Editor** in the left sidebar
   3. Click **New Query**
   4. Open `migrations/001_initial_schema.sql` in your editor, copy its entire contents, and paste it into the SQL Editor
   5. Click **Run** (or press `Cmd+Enter` / `Ctrl+Enter`)
   6. Verify the migration succeeded (you should see "Success" message)
   7. Repeat steps 3-6 for `migrations/003_initial_settings.sql`
   8. Repeat steps 3-6 for `migrations/004_add_full_title_column.sql`

   **Method 3: Using psql directly (For advanced users)**

```bash
   # Get your database connection string from Supabase dashboard:
   # Settings → Database → Connection string → URI
   
   # Run each migration in order using psql
   psql "$DATABASE_URL" < migrations/001_initial_schema.sql
   psql "$DATABASE_URL" < migrations/003_initial_settings.sql
   psql "$DATABASE_URL" < migrations/004_add_full_title_column.sql
   ```

   **Migration Order (Applied automatically by script):**
   1. `001_initial_schema.sql` - Creates all tables, indexes, and constraints (REQUIRED)
   2. `003_initial_settings.sql` - Inserts initial bot settings (REQUIRED)
   3. `004_add_full_title_column.sql` - Adds full_title column for new title management (REQUIRED)

5. **Configure Bot Privacy Settings (Required for Group Messages):**

   For the bot to process messages from @HowGayBot in group chats, you need to disable privacy mode:
   
   1. Open a chat with [@BotFather](https://t.me/BotFather) on Telegram
   2. Send `/mybots` and select your bot
   3. Click on **"Bot Settings"**
   4. Select **"Group Privacy"**
   5. Choose **"Turn off"** to disable privacy mode
   6. **Important:** Remove the bot from the group and add it back for the settings to take effect
   
   **Note:** Without disabling privacy mode, the bot can only see messages directed at it (commands or mentions). Messages sent "via @HowGayBot" won't be visible to the bot.

6. Run the bot:

**Important: Before starting, make sure no other bot instances are running!**

**Using pipenv:**
```bash
# Make sure you're in the pipenv shell first
pipenv shell

# Then run the bot
python -m src.presentation.main
```

**Or run directly with pipenv:**
```bash
pipenv run python -m src.presentation.main
```

**Using pip:**
```bash
python -m src.presentation.main
```

**If you get "Conflict: terminated by other getUpdates request" error:**

This means another bot instance is already running. To fix:

1. **Stop all running bot instances:**
   ```bash
   # Option 1: Use the helper script
   ./scripts/stop_bot.sh
   
   # Option 2: Manual kill
   pkill -f 'python.*bot'
   pkill -f 'src.presentation.main'
   
   # Option 3: Find and kill specific process
   ps aux | grep 'python.*bot' | grep -v grep
   kill <PID>
   ```

2. **Check for deployed instances:**
   - If deployed on Railway/Heroku/etc., stop it there
   - Check your deployment platform dashboard

3. **Check for webhooks:**
   - The bot code automatically deletes webhooks on startup
   - If the error persists, check your bot settings in Telegram

4. **Wait a few seconds** after stopping instances before starting again

## Database Setup

1. Create a Supabase project at https://supabase.com
2. Get your project credentials:
   - Go to **Settings** → **API**
   - Copy your **Project URL** (use for `SUPABASE_URL` in `.env`)
   - Copy your **anon/public** key (use for `SUPABASE_KEY` in `.env`)
   - Go to **Settings** → **Database** → **Connection string** → **URI**
   - Copy the connection string and add it as `DATABASE_URL` in `.env` (replace `[YOUR-PASSWORD]` with actual password)
3. Run the migration scripts using the automated migration runner:
   ```bash
   pipenv run python scripts/run_migrations.py
   ```
   
   Or manually via Supabase SQL Editor (see [Setup](#setup) section above for details):
   - `migrations/001_initial_schema.sql` - Creates all tables and indexes
   - `migrations/003_initial_settings.sql` - Creates initial bot settings
   - `migrations/004_add_full_title_column.sql` - Adds full_title column to users table

## Admin Configuration

To set up admin access for the bot, you need to configure at least one of the following in your `.env` file:

### Option 1: Using Telegram User ID (Recommended)

1. **Get your Telegram User ID:**
   - Start a conversation with [@userinfobot](https://t.me/userinfobot) on Telegram
   - The bot will reply with your user ID (a number like `123456789`)
   - Copy this number

2. **Add to `.env`:**
   ```bash
   ADMIN_USER_ID=123456789
   ```

### Option 2: Using Telegram Username (Fallback)

1. **Get your Telegram username:**
   - Go to Telegram Settings → Profile
   - Find your username (without the `@` symbol, e.g., `john_doe`)

2. **Add to `.env`:**
   ```bash
   ADMIN_USERNAME=john_doe
   ```

### Option 3: Both (More Secure)

You can set both for redundancy:
```bash
ADMIN_USER_ID=123456789
ADMIN_USERNAME=john_doe
```

**Important Notes:**
- At least one of `ADMIN_USER_ID` or `ADMIN_USERNAME` must be set
- If both are set, the bot will check user ID first (more secure), then username as fallback
- User ID is more secure because usernames can be changed, but user IDs are permanent
- Admin users have access to admin commands:
  - `/lock_title @username` - Lock a user's title
  - `/unlock_title @username` - Unlock a user's title
  - `/set_full_title @username <title>` - Set a user's full title manually
  - `/set_global_average_period <days>` - Set the statistics calculation period
  - Access to Settings button in the bot interface

## Migration from Google Sheets

If you have existing data in Google Sheets:

1. Export Google Sheets data to CSV format
2. Run migration script:
```bash
# Dry run (preview changes)
python migrations/002_migrate_google_sheets.py --dry-run path/to/export.csv

# Execute migration
python migrations/002_migrate_google_sheets.py --execute path/to/export.csv

# Rollback (if needed)
python migrations/002_migrate_google_sheets.py --rollback <batch_id>
```

## Commands

### User Commands
- `/start` - Welcome message and command overview
- `/me` - Show your statistics
- `/who @username` - Show user statistics
- `/leaderboard` - Show leaderboard sorted by title letter count
- `/stats [days]` - Show global statistics (optional period in days)
- `/help` - Show help message

### Admin Commands (Admin only)
To use admin commands, you must first configure admin access (see [Admin Configuration](#admin-configuration) section above).

- `/lock_title @username` - Lock user's title (prevents auto-updates)
- `/unlock_title @username` - Unlock user's title (allows auto-updates)
- `/set_full_title @username <title>` - Set a user's full title manually
- `/set_global_average_period <days>` - Set statistics period (0 = all-time)

**Admin Interface:**
- Admin users see a **Settings** button (⚙️) in the main menu
- Click Settings to see all available admin commands
- Use the **Back** button (⬅️) to return to the main menu

## Railway Deployment

1. Create a Railway project
2. Connect your repository
3. Set environment variables in Railway dashboard
4. Railway will automatically detect the `Procfile` and deploy

The bot will start using `python -m src.presentation.main`

## Development

### Running Tests

**Using pipenv:**
```bash
# Install dev dependencies (if you have requirements-dev.txt)
pipenv install --dev

# Run tests
pipenv run pytest

# Run with coverage
pipenv run pytest --cov=src --cov-report=html
```

**Using pip:**
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality

**Using pipenv:**
```bash
pipenv run black src/
pipenv run ruff check src/
pipenv run mypy src/
```

**Using pip:**
```bash
# Format code
black src/

# Lint code
ruff check src/

# Type check
mypy src/
```

## Project Structure

- `src/domain/` - Domain layer (entities, value objects, services, repositories interfaces)
- `src/application/` - Application layer (use cases, application services)
- `src/infrastructure/` - Infrastructure layer (Supabase repositories, config, jobs, logging)
- `src/presentation/` - Presentation layer (Telegram handlers, keyboards, main entry point)
- `migrations/` - Database migration scripts
- `tests/` - Test files (unit, integration, e2e)
- `docs/` - Documentation

## License

[Add your license here]
