# Telegram Bot - Title Management with Message Monitoring

A Clean Architecture Telegram bot that monitors @HowGayBot messages, tracks user percentages, and manages titles based on dynamic letter-counting rules.

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Setup](#setup)
- [Database Setup](#database-setup)
- [Admin Configuration](#admin-configuration)
- [Commands](#commands)
- [Title Management System](#title-management-system)
- [Bot Privacy Mode](#bot-privacy-mode)
- [Deployment](#deployment)
- [Development](#development)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

## Features

- **Message Monitoring**: Automatically processes messages from @HowGayBot in group chats (including messages sent "via @HowGayBot")
- **Title Management**: Dynamic title updates based on percentage rules using a full-title system
- **User Statistics**: View personal stats including current title, percentage, position, and trends
- **Leaderboard**: Sort users by title letter count (ascending order)
- **Global Statistics**: Daily/weekly/monthly trends and configurable global averages
- **Admin Tools**: Comprehensive admin commands for user and title management
- **Multi-language Support**: English and Russian
- **Timezone Support**: Configurable timezone for daily reset logic
- **Title Locking**: Prevent automatic title updates for specific users
- **Default Titles**: Set default titles for new users

## How It Works

The bot monitors group chat messages and automatically processes messages from @HowGayBot. When a message is detected:

1. **Message Detection**: The bot identifies messages from or sent via @HowGayBot
2. **Percentage Extraction**: Extracts the percentage value (0-100) from the message
3. **User Identification**: Identifies the target user from the message context
4. **Title Calculation**: Calculates the displayed title based on the user's `full_title` and the percentage
5. **Daily Processing**: Only processes the first message per user per day (timezone-aware)
6. **Statistics Update**: Updates user statistics and creates daily snapshots

## Architecture

This project follows Clean Architecture principles with clear separation of concerns:

```
src/
├── domain/           # Business logic (entities, value objects, services, repositories interfaces)
├── application/      # Use cases and application services
├── infrastructure/   # External concerns (database, config, jobs, logging)
└── presentation/     # Telegram bot handlers and UI
```

### Key Components

- **Domain Layer**: Core business logic, entities, and domain services
- **Application Layer**: Use cases that orchestrate domain logic
- **Infrastructure Layer**: Supabase repositories, configuration, scheduled jobs
- **Presentation Layer**: Telegram bot handlers, keyboards, and main entry point

## Setup

### Prerequisites

- Python 3.11.12
- Supabase account and project
- Telegram Bot Token (from @BotFather)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd check_titles_tg_bot
```

2. **Install dependencies:**

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

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

**Required environment variables:**
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase API key
- `ADMIN_USER_ID` - Your Telegram user ID (recommended)
- `ADMIN_USERNAME` - Your Telegram username (fallback)
- `DATABASE_URL` - Database connection string for migrations

4. **Run database migrations:**

   **Method 1: Automated Migration Script (Recommended)**

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
   6. Replace `[YOUR-PASSWORD]` with your actual database password
   7. Add it to your `.env` file as `DATABASE_URL` (wrap in quotes if password has special characters)
   
   **Important Notes:**
   - If you get "nodename nor servname provided" error: Your project might require connection pooling (port 6543)
   - Password with special characters: The migration script automatically URL-encodes special characters
   - Example: If your password is `#M#83bNY63NAGasDXrmp`, use it directly:
     ```
     DATABASE_URL="postgresql://postgres:#M#83bNY63NAGasDXrmp@project.supabase.co:6543/postgres"
     ```

   Then run the automated migration script:

   **Using pipenv:**
   ```bash
   pipenv run python scripts/run_migrations.py
   ```

   **Using pip:**
   ```bash
   python scripts/run_migrations.py
   ```

   The script will automatically detect and run pending migrations in the correct order.

   **Dry run mode** (preview without applying):
   ```bash
   python scripts/run_migrations.py --dry-run
   ```

   **Method 2: Manual Migration via Supabase SQL Editor**

   1. Go to your Supabase project dashboard: https://app.supabase.com
   2. Navigate to **SQL Editor** in the left sidebar
   3. Click **New Query**
   4. Open each migration file in order and run them:
      - `migrations/001_initial_schema.sql`
      - `migrations/003_initial_settings.sql`
      - `migrations/004_add_full_title_column.sql`
      - `migrations/005_add_default_title_setting.sql` (if exists)

   **Migration Order:**
   1. `001_initial_schema.sql` - Creates all tables, indexes, and constraints (REQUIRED)
   2. `003_initial_settings.sql` - Inserts initial bot settings (REQUIRED)
   3. `004_add_full_title_column.sql` - Adds full_title column for new title management (REQUIRED)
   4. `005_add_default_title_setting.sql` - Adds default title setting (if applicable)

5. **Configure Bot Privacy Settings** (Required for Group Messages)

   See [Bot Privacy Mode](#bot-privacy-mode) section below for detailed instructions.

6. **Run the bot:**

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
3. Run migrations (see [Setup](#setup) section above for details)

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
- Admin users have access to all admin commands (see [Commands](#commands) section)

## Commands

### User Commands

- `/start` - Welcome message and command overview
- `/register` - Register yourself in the system
- `/me` - Show your personal statistics (title, percentage, position, trends)
- `/who @username` - Show statistics for a specific user
- `/leaderboard` - Show leaderboard sorted by title letter count (ascending)
- `/stats [days]` - Show global statistics (optional period in days, default: all-time)
- `/help` - Show help message
- `/chat_id` - Display the current chat ID (useful for admin setup)

### Admin Commands

**Note:** To use admin commands, you must first configure admin access (see [Admin Configuration](#admin-configuration) section above).

- `/lock_title @username` - Lock a user's title (prevents automatic updates)
- `/unlock_title @username` - Unlock a user's title (allows automatic updates)
- `/set_full_title @username <title>` - Set a user's full title manually (supports spaces)
- `/set_title @username <title>` - Alias for `/set_full_title`
- `/set_full_title_for_all <title>` - Set the full title for all users at once (supports spaces)
- `/set_global_average_period <days>` - Set statistics calculation period (0 = all-time)
- `/add_user @username [chat_id]` - Add a user to the system manually
- `/set_default_title <title>` - Set the default title for new users
- `/migrate_users_to_default_title` - Migrate all users without titles to the default title
- `/delete_user @username` - Delete a user from the system

**Admin Interface:**
- Admin users see a **Settings** button (⚙️) in the main menu
- Click Settings to see all available admin commands
- Use the **Back** button (⬅️) to return to the main menu

## Title Management System

The bot uses a **full-title based system** where each user has a `full_title` (set by admin) and a `title` (calculated displayed title).

### How It Works

1. **Full Title**: Set by admin using `/set_full_title` or `/set_full_title_for_all`. This is the base title that contains the complete text.
2. **Displayed Title**: Automatically calculated from the `full_title` based on percentage rules. The displayed title is a substring of the full title.

### Title Calculation Rules

The displayed title is calculated by incrementing or decrementing the current title based on the percentage. The title is always a substring of the `full_title` and can become empty.

- **0%** → Add 3 letters to current title (from `full_title`)
- **1-5%** → Add 1 letter to current title (from `full_title`)
- **95-99%** → Remove 1 letter from current title (can become empty)
- **100%** → Remove N letters from current title, where N = active_user_count (if result is negative, title becomes empty)
- **Other percentages** → No change (title remains the same)

**Examples:**
- If `full_title` = "Super Gay Title" (13 letters):
  - Current title: "Super Gay Tit" (12 letters)
    - 0% → "Super Gay Title" (12 + 3 = 15, capped at 13 letters = full title)
    - 1-5% → "Super Gay Titl" (12 + 1 = 13 letters = full title)
    - 95-99% → "Super Gay Ti" (12 - 1 = 11 letters)
    - 100% → Depends on active user count (e.g., if 5 active users → 12 - 5 = 7 letters = "Super Ga")
  
  - Current title: "Su" (2 letters)
    - 0% → "Super" (2 + 3 = 5 letters)
    - 1-5% → "Sup" (2 + 1 = 3 letters)
    - 95-99% → "S" (2 - 1 = 1 letter)
    - 100% → "" (empty, if 2 - N ≤ 0)

### Title Processing

- **First Message Per Day**: The bot only processes the first @HowGayBot message per user per day (timezone-aware)
- **Title Locking**: Admins can lock titles to prevent automatic updates
- **Default Titles**: Admins can set default titles for new users

## Bot Privacy Mode

By default, Telegram bots in group chats operate in "privacy mode," meaning they only receive messages that are:
- Direct commands (starting with `/`)
- Messages that mention the bot by its username
- Replies to the bot's own messages

To allow this bot to monitor all messages in a group (including those from @HowGayBot), you **must disable privacy mode** via @BotFather.

**Steps to disable Group Privacy:**

1. **Contact @BotFather**: Open a chat with [@BotFather](https://t.me/BotFather) on Telegram
2. **Select Your Bot**: Send the command `/mybots` and choose your bot from the list
3. **Access Bot Settings**: Click on "Bot Settings"
4. **Change Group Privacy**: Select "Group Privacy" and then choose "Turn off"

**Important**: After disabling privacy mode, it is recommended to **remove your bot from the group and add it back** to ensure the new settings take effect.

**Note:** Without disabling privacy mode, the bot can only see messages directed at it (commands or mentions). Messages sent "via @HowGayBot" won't be visible to the bot.

## Deployment

### Railway Deployment

1. Create a Railway project
2. Connect your repository
3. Set environment variables in Railway dashboard (same as `.env` file)
4. Railway will automatically detect the `Procfile` and deploy

The bot will start using `python -m src.presentation.main`

### Environment Variables for Deployment

Make sure to set all required environment variables in your deployment platform:

- `TELEGRAM_BOT_TOKEN`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `ADMIN_USER_ID` (recommended)
- `ADMIN_USERNAME` (optional fallback)
- `DATABASE_URL` (for migrations, if needed)

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

```
check_titles_tg_bot/
├── src/
│   ├── domain/           # Domain layer (entities, value objects, services, repositories interfaces)
│   ├── application/      # Application layer (use cases, application services)
│   ├── infrastructure/   # Infrastructure layer (Supabase repositories, config, jobs, logging)
│   └── presentation/     # Presentation layer (Telegram handlers, keyboards, main entry point)
├── migrations/           # Database migration scripts
├── tests/                # Test files (unit, integration, e2e)
├── docs/                 # Documentation
├── scripts/              # Utility scripts (migrations, bot management)
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
├── Procfile             # Deployment configuration
└── README.md            # This file
```

### Key Directories

- `src/domain/` - Core business logic, entities, value objects, domain services
- `src/application/` - Use cases and application services
- `src/infrastructure/` - External concerns (Supabase repositories, configuration, scheduled jobs, logging)
- `src/presentation/` - Telegram bot handlers, keyboards, UI components, main entry point
- `migrations/` - Database migration scripts (SQL and Python)
- `tests/` - Test files organized by type (unit, integration, e2e)

## Troubleshooting

### Common Issues

1. **"Conflict: terminated by other getUpdates request"**
   - Another bot instance is running
   - Stop all instances (local and deployed)
   - Wait a few seconds before restarting

2. **Bot not receiving @HowGayBot messages**
   - Check that bot privacy mode is disabled (see [Bot Privacy Mode](#bot-privacy-mode))
   - Remove and re-add bot to the group after changing privacy settings

3. **Database connection errors**
   - Verify `DATABASE_URL` is correct
   - Check if you need connection pooling (port 6543) vs direct connection (port 5432)
   - Ensure password is URL-encoded if it contains special characters

4. **Migrations failing**
   - Check database connection string
   - Verify migrations are run in correct order
   - Check Supabase project settings and permissions

5. **Admin commands not working**
   - Verify `ADMIN_USER_ID` or `ADMIN_USERNAME` is set correctly
   - Check that your user ID/username matches the configured admin
   - Use `/chat_id` command to verify your user ID

6. **Title not updating**
   - Verify user has a `full_title` set (use `/set_full_title`)
   - Check if title is locked (use `/unlock_title` if needed)
   - Verify bot is processing messages (check logs)

### Getting Help

- Check the logs for error messages
- Verify all environment variables are set correctly
- Ensure database migrations have been run
- Check that bot privacy mode is disabled

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

## License

[Add your license here]
