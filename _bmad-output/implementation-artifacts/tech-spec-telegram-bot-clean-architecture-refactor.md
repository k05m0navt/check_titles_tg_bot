---
title: 'Telegram Bot Refactoring - Clean Architecture with Message Monitoring + User Registration'
slug: 'telegram-bot-clean-architecture-refactor'
created: '2026-01-10T14:05:10Z'
updated: '2026-01-10T16:00:00Z'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.11.12', 'python-telegram-bot 20.7', 'Supabase 2.0.0 (PostgreSQL)', 'Railway', 'pytz 2024.1', 'pydantic 2.5.0', 'APScheduler 3.10.0', 'structlog 23.1.0']
files_to_modify: ['bot.py', 'requirements.txt', '.gitignore']
files_to_create: ['src/domain/**', 'src/application/**', 'src/infrastructure/**', 'src/presentation/**', 'migrations/**', 'tests/**', 'README.md', 'Procfile', '.env.example']
code_patterns: ['Clean Architecture', 'Repository Pattern', 'Manual Dependency Injection', 'Use Case Pattern', 'Async/Await', 'Domain Events']
test_patterns: ['pytest 7.4.0', 'pytest-asyncio 0.21.0', 'pytest-cov 4.1.0', 'Unit Tests', 'Integration Tests', 'E2E Tests with Mocked Telegram API']
---

# Tech-Spec: Telegram Bot Refactoring - Clean Architecture with Message Monitoring

**Created:** 2026-01-10T14:05:10Z

## Overview

### Problem Statement

The current bot implementation is monolithic, uses Google Sheets for data storage, lacks message monitoring from other bots, has no @ command system, missing proper architecture separation, and lacks critical features including: statistics/analytics, admin commands, multi-language support, timezone configuration, and error handling. Additionally, the bot lacks user registration functionality when added to groups, admin ability to add users, and a default title system where all users share a common base title set by admin. The bot needs a complete refactoring to Clean Architecture principles while adding new functionality for monitoring @HowGayBot messages, implementing letter-based title management based on percentage ranges, user registration system, and providing a robust command system with inline keyboards similar to @HowGayBot's interface.

### Solution

Refactor the bot to Clean Architecture with clear separation of concerns (Domain, Application, Infrastructure, Presentation layers). Migrate from Google Sheets to Supabase (PostgreSQL). Implement message monitoring from @HowGayBot to extract percentage values and update user titles based on letter-based rules. Add @ command system with inline keyboard buttons. Implement admin-only commands for title locking and settings management. Add comprehensive statistics (daily/weekly/monthly trends, global averages). Support multi-language and timezone configuration through settings. Implement first-message-per-day tracking per user. Sort users by number of letters in their titles.

### Scope

**In Scope:**

1. **Clean Architecture Implementation**
   - Domain layer: Entities, Value Objects, Domain Services
   - Application layer: Use Cases, Application Services
   - Infrastructure layer: Database (Supabase), Telegram API adapters
   - Presentation layer: Command handlers, Callback handlers, Message handlers

2. **Database Migration**
   - Migrate from Google Sheets to Supabase (PostgreSQL)
   - Schema design for users, messages, statistics, settings
   - Migration scripts

3. **Message Monitoring**
   - Listen to messages from @HowGayBot in groups/channels
   - Parse percentage values (e.g., "I am 90% gay!")
   - Track by username of users who use our bot
   - Only process first message per day per user (timezone-aware)

4. **Letter-Based Title Management**
   - 0% → Add 3 letters to title
   - 1-5% → Add 1 letter to title
   - 95-99% → Remove 1 letter from title
   - 100% → Remove number of letters equal to number of active bot users
   - Manual title locking (admin only) - locked titles never change automatically

5. **@ Command System**
   - Inline keyboard buttons when users type @BotName
   - Commands: "📊 My Stats", "👥 Leaderboard", "📝 Help"
   - Admin-only commands: "⚙️ Settings", "🔒 Lock Title" (shown conditionally)

6. **Admin Features**
   - Admin set via environment variable (username)
   - Lock/unlock user titles
   - Manage settings
   - View statistics

7. **Statistics & Analytics**
   - Daily/weekly/monthly percentage trends per user
   - Global statistics (average percentage across all users)
   - Title distribution
   - Historical data storage

8. **Multi-Language Support**
   - Settings-based language switching
   - Support for English and Russian initially
   - Localization infrastructure

9. **Timezone Configuration**
   - Configurable timezone setting
   - Use for daily reset logic

10. **User Sorting**
    - Sort users by number of letters in title (ascending/descending)
    - Display in leaderboard and list views

11. **User Registration & Group Management**
    - When bot is added to a group: Users can register themselves via `/register` or `/start` command
    - Admin can add users manually via `/add_user @username <chat_id>` command (admin only) - requires chat_id because Telegram Bot API cannot resolve username to user_id without chat context
    - Welcome message when bot joins a group
    - Note: Group membership tracking (which users in which groups) is out of scope for initial implementation - users are registered globally, not per-group

12. **Default Title System**
    - Admin sets a default/base title in bot settings (stored in `bot_settings` table with key `default_title`)
    - Default title must be validated: max length 500 characters, no control characters
    - All new users automatically get this default title as their `full_title` when they register
    - If default title is empty, new users get empty `full_title` (admin must set it first)
    - Admin can update default title via `/set_default_title <title>` command (validates length and characters)
    - When default title is updated, existing users are NOT automatically updated (they keep their current `full_title`)
    - Admin can optionally update all existing users via `/migrate_users_to_default_title` command (explicit opt-in, not automatic)
    - New registrations always use current default title from settings

13. **Error Handling**
    - Comprehensive error handling throughout all layers
    - Logging infrastructure
    - User-friendly error messages

14. **Documentation**
    - README.md with setup instructions
    - Railway deployment configuration
    - Environment variables documentation

15. **Railway Deployment**
    - Configuration for Railway platform
    - Environment variables setup
    - Database connection handling

**Out of Scope:**

- Real-time push notifications
- Web dashboard interface
- Multiple bot monitoring (only @HowGayBot)
- User authentication system (using Telegram's built-in auth)
- Mobile app interface
- Payment integration
- Bot-to-bot direct communication

## Context for Development

### Codebase Patterns

**Current State (Investigated):**
- Monolithic single-file architecture (`bot.py` - 136 lines)
- Google Sheets integration via `gspread` (direct API calls)
- Direct handler functions without separation:
  - `async def me()`, `async def who()`, `async def all_users()`, `async def buttons()`
- Russian language hardcoded in strings (e.g., "Тебя нет в таблице 😢", "Используй: /who @username")
- No error handling beyond basic checks (`if not context.args`)
- No logging infrastructure (no log statements found)
- Environment variables accessed directly via `os.environ`:
  - `TELEGRAM_BOT_TOKEN`
  - `GOOGLE_SHEET_ID`
  - `GOOGLE_CREDENTIALS` (JSON string)
- No test files or test infrastructure
- No project-context.md or coding standards
- Simple `.gitignore` (only `.env` and `credentials.json`)
- No Railway-specific configuration files yet
- **Confirmed: Clean Slate** - No legacy constraints, build Clean Architecture from scratch

**Code Style Observed:**
- Uses async/await pattern (consistent with python-telegram-bot 20.7)
- Function naming: lowercase with underscores (`get_data`, `build_keyboard`, `format_user`)
- No type hints
- No docstrings beyond basic function comments
- Section dividers with comments: `# -----------------------------`

**Target Patterns:**

1. **Clean Architecture Layers:**
   ```
   src/
   ├── domain/          
   │   ├── entities/          # User, Message
   │   ├── value_objects/     # Title, Percentage, Timezone, Language
   │   ├── services/          # TitleCalculationService
   │   └── repositories/      # Abstract interfaces
   ├── application/     
   │   ├── use_cases/         # UpdateTitleUseCase, GetLeaderboardUseCase, etc.
   │   └── services/          # MessageParsingService, StatisticsService
   ├── infrastructure/  
   │   ├── database/          # SupabaseRepository implementations
   │   ├── telegram/          # TelegramAdapter
   │   ├── config/            # SettingsManager
   │   └── jobs/              # Scheduled jobs (APScheduler)
   └── presentation/    
       ├── handlers/          # CommandHandlers, MessageHandler, CallbackHandler
       ├── keyboards/         # InlineKeyboardBuilder
       └── main.py            # Application entry point (replaces bot.py)
   ```

2. **Repository Pattern:**
   - Abstract repository interfaces in `domain/repositories/`
   - Concrete implementations in `infrastructure/database/repositories/`
   - Example: `IUserRepository` → `SupabaseUserRepository`

3. **Dependency Injection:**
   - Manual dependency injection via constructor (start simple)
   - Pass dependencies as constructor parameters
   - Can refactor to DI container later if needed

4. **Use Case Pattern:**
   - Each feature as a use case class with `execute()` method
   - Clear input/output contracts (DTOs or dataclasses)
   - Example: `UpdateTitleUseCase.execute(user_id: int, percentage: int) -> None`

5. **Error Handling:**
   - Custom exception hierarchy in `domain/exceptions.py`
   - Error boundaries at presentation layer (try/except in handlers)
   - Structured logging with `structlog` or `loguru`

6. **Async/Await Pattern:**
   - Maintain async/await throughout (consistent with python-telegram-bot)
   - All repositories return awaitable types
   - Use asyncio for concurrent operations

7. **Type Hints:**
   - Add type hints to all functions (Python 3.11 supports modern typing)
   - Use `typing` module for complex types
   - Optional: Use `mypy` for static type checking

### Files to Reference

| File | Purpose | Status |
| ---- | ------- | ------ |
| `bot.py` | Current monolithic implementation to refactor | Will be replaced by `src/presentation/main.py` |
| `requirements.txt` | Current dependencies (`python-telegram-bot==20.7`, `gspread`) | Update with new dependencies |
| `runtime.txt` | Python version (3.11.12) for Railway | Keep as-is |
| `.env` | Environment variables (currently: TELEGRAM_BOT_TOKEN, GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS) | Create `.env.example` template |
| `.gitignore` | Current: `/.env`, `/credentials.json` | Add new ignores: `__pycache__/`, `*.pyc`, `.pytest_cache/`, etc. |

**Files to Create (Clean Architecture Structure):**

| Category | Files |
| -------- | ----- |
| **Domain Layer** | `src/domain/entities/user.py`, `src/domain/value_objects/title.py`, `src/domain/value_objects/percentage.py`, `src/domain/repositories/user_repository.py`, `src/domain/exceptions.py` |
| **Application Layer** | `src/application/use_cases/*.py`, `src/application/services/message_parser.py`, `src/application/services/statistics_service.py` |
| **Infrastructure Layer** | `src/infrastructure/database/supabase_client.py`, `src/infrastructure/database/repositories/*.py`, `src/infrastructure/telegram/adapter.py`, `src/infrastructure/config/settings.py`, `src/infrastructure/jobs/*.py` |
| **Presentation Layer** | `src/presentation/handlers/command_handlers.py`, `src/presentation/handlers/message_handler.py`, `src/presentation/handlers/callback_handler.py`, `src/presentation/handlers/chat_member_handler.py` (NEW), `src/presentation/keyboards/inline_keyboard.py`, `src/presentation/main.py` |
| **Migrations** | `migrations/001_initial_schema.sql`, `migrations/002_migrate_google_sheets.py`, `migrations/003_initial_settings.sql`, `migrations/005_add_default_title_setting.sql` (NEW) |
| **Tests** | `tests/unit/`, `tests/integration/`, `tests/e2e/`, `tests/conftest.py`, `pytest.ini` |
| **Configuration** | `README.md`, `Procfile` (for Railway), `.env.example`, `pyproject.toml` or `setup.py` |
| **Documentation** | `docs/database_schema.md`, `docs/architecture.md`, `docs/migration_guide.md` |

**Files to Modify for New Features:**

| File | Changes Needed |
| ---- | -------------- |
| `src/presentation/handlers/command_handlers.py` | Add `handle_register()`, `handle_add_user()` (admin), `handle_set_default_title()` (admin), update `handle_start()` to optionally register |
| `src/presentation/main.py` | Register `ChatMemberHandler` or `MessageHandler` with `filters.StatusUpdate.NEW_CHAT_MEMBERS` for bot-added-to-group events |
| `src/domain/repositories/settings_repository.py` | Add `get_default_title()` and `set_default_title()` methods |
| `src/infrastructure/database/repositories/supabase_settings_repository.py` | Implement `get_default_title()` and `set_default_title()` methods |
| `src/application/use_cases/register_user_use_case.py` | NEW: Create use case for user registration with default title |
| `src/application/use_cases/add_user_use_case.py` | NEW: Create use case for admin to add users manually |
| `src/application/use_cases/set_default_title_use_case.py` | NEW: Create use case for admin to set default title |
| `migrations/003_initial_settings.sql` | Add `default_title` setting with empty string as default |

### Technical Decisions

1. **Database: Supabase (PostgreSQL)**
   - PostgreSQL-compatible, cloud-hosted
   - Use `supabase-py` client library (version 2.0.0+) for direct PostgreSQL connection
   - Avoid REST API for better performance and transaction support
   - Built-in authentication and real-time features (not required for this project, but available)
   - Connection pooling via `supabase-py` for optimal performance

2. **Architecture: Clean Architecture**
   - Separation of concerns across 4 layers (Domain, Application, Infrastructure, Presentation)
   - Testability: Mock dependencies easily with interfaces
   - Maintainability: Clear boundaries, single responsibility
   - Technology independence: Swap Supabase or Telegram API without affecting domain

3. **Message Parsing: Regex-based with Validation**
   - Pattern: `r"I am (\d+)% gay!"` (exact match from @HowGayBot only)
   - Extract numeric percentage values using regex groups
   - Validate range: Must be 0-100 (reject negative or >100)
   - Strict filtering: Only process if `message.from_user.username == "HowGayBot"`

4. **Title Management: Full Title Base with Substring Strategy**
   - Admin sets a `full_title` (base title) for each user (e.g., "Super Gay Title")
   - Displayed `title` is calculated as a substring of `full_title` based on percentage rules
   - Letter counting: Spaces excluded, alphanumeric only (regex: `r'[^a-zA-Z0-9]'`)
   - Percentage rules determine how many letters to show from the full_title:
     - 0% → Show first 3 letters from full_title
     - 1-5% → Show first 1 letter from full_title
     - 95-99% → Show (full_title_letters - 1) letters from full_title
     - 100% → Show (full_title_letters - active_user_count) letters from full_title
   - Lock mechanism: `title_locked` flag prevents automatic changes (admin can still manually change full_title)
   - Track title history in `title_history` table for statistics
   - Edge case: If calculated letter count < 0, set to empty string
   - Edge case: If full_title is not set, displayed title remains empty until admin sets it

5. **First Message Tracking: Date-based with Timezone Support**
   - Store `last_processed_date` per user (DATE type, not TIMESTAMP)
   - Use configured user timezone (`pytz` library) for date calculations
   - Process message if `message_date.date() != last_processed_date.date()` (timezone-aware)
   - Handle edge case: Messages at 11:59 PM and 12:01 AM on different dates → both processed

6. **Language System: Settings-based with Database Storage**
   - Store user language preference in `users.language` column ('en' or 'ru')
   - Use translation keys/strings (simple dict-based or i18n library)
   - Support for English and Russian initially
   - Default: English (configurable via bot_settings)

7. **Admin System: Environment Variable with Database Extension Path**
   - Single admin username from `ADMIN_USERNAME` env var
   - Admin commands protected by username check: `if username == os.environ["ADMIN_USERNAME"]`
   - Future: Extend to multi-admin via `bot_settings` table (stored as JSON array)

8. **Job Scheduling: APScheduler for Background Tasks**
   - Use `APScheduler` for scheduled jobs (daily snapshots, statistics calculation)
   - Async-compatible scheduler for python-telegram-bot's async context
   - Configure timezone-aware scheduling

9. **Logging: Structured Logging**
   - Use `structlog` or `loguru` for structured logging
   - Log levels: DEBUG, INFO, WARNING, ERROR
   - Log to both file and console
   - Railway logging integration via stdout

10. **Type Safety: Progressive Type Hints**
    - Add type hints to all new code (Python 3.11 supports modern typing)
    - Use `typing` module for complex types
    - Optional: Use `mypy` for static type checking (development only)

11. **Code Quality Tools:**
    - `black` for code formatting (consistent style)
    - `ruff` for linting (fast, modern linter)
    - `mypy` for type checking (optional, for development)
    - `pytest` with `pytest-cov` for testing and coverage

12. **Railway Deployment:**
    - Use `Procfile` with command: `python -m src.presentation.main`
    - Or use `railway.json` for configuration
    - Environment variables set via Railway dashboard
    - Health check endpoint (optional, but recommended)

13. **User Registration: Command-Based with Default Title**
    - Users register via `/register` command (separate from `/start` to allow welcome without registration)
    - `/start` shows welcome message; `/register` actually registers the user
    - Registration creates user with default title from `bot_settings.default_title` as `full_title`
    - If user already exists, registration returns success message (idempotent)
    - Displayed title (`title`) starts as empty until first percentage message is processed

14. **Group Events: Chat Member Updates**
    - Use `MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS)` to detect when bot is added to group
    - When bot is added: Send welcome message to group explaining registration process
    - Use `ChatMemberUpdated` updates (python-telegram-bot 20.7+) for tracking bot's own membership status
    - Track bot's group membership in memory (optional: store in database for persistence)

15. **Admin User Management**
    - Admin command `/add_user @username` resolves username to Telegram user ID and creates user
    - If username doesn't exist in Telegram: Return error message to admin
    - If user already exists: Return success (idempotent)
    - Admin command `/set_default_title <title>` updates `bot_settings.default_title`
    - Default title is used for all NEW registrations (doesn't affect existing users)

## Implementation Plan

### Tasks

**Phase 1: Foundation & Database (Week 1)**

- [ ] **Task 1.1: Project Structure Setup**
  - **Files**: Create directory structure `src/domain/`, `src/application/`, `src/infrastructure/`, `src/presentation/`, `tests/unit/`, `tests/integration/`, `tests/e2e/`, `migrations/`, `docs/`
  - **Action**: Create `__init__.py` files in each package directory
  - **Notes**: Follow Python package structure conventions

- [ ] **Task 1.2: Update Dependencies**
  - **File**: `requirements.txt`
  - **Action**: Replace existing dependencies with: `python-telegram-bot==20.7`, `supabase==2.0.0`, `python-dotenv==1.0.0`, `pytz==2024.1`, `pydantic==2.5.0`, `APScheduler==3.10.0`, `structlog==23.1.0`
  - **File**: Create `requirements-dev.txt`
  - **Action**: Add development dependencies: `pytest==7.4.0`, `pytest-asyncio==0.21.0`, `pytest-cov==4.1.0`, `mypy==1.5.0`, `black==23.7.0`, `ruff==0.0.285`
  - **Notes**: Pin exact versions for reproducibility

- [ ] **Task 1.3: Environment Configuration**
  - **File**: Create `.env.example`
  - **Action**: Document all environment variables: `TELEGRAM_BOT_TOKEN`, `SUPABASE_URL`, `SUPABASE_KEY`, `ADMIN_USERNAME`, `GOOGLE_SHEET_ID` (migration only), `GOOGLE_CREDENTIALS` (migration only)
  - **File**: Update `.gitignore`
  - **Action**: Add: `__pycache__/`, `*.pyc`, `*.pyo`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `*.log`, `.env`
  - **Notes**: Never commit `.env` file

- [ ] **Task 1.4: Database Schema Creation**
  - **File**: Update `migrations/001_initial_schema.sql` or create new migration `migrations/004_add_full_title_column.sql`
  - **Action**: Add `full_title` column to `users` table: `full_title TEXT NOT NULL DEFAULT ''` (admin sets this, displayed title is calculated from it)
  - **Action**: Ensure all 5 tables (`users`, `daily_snapshots`, `title_history`, `bot_settings`, `statistics_cache`) exist with indexes and constraints
  - **File**: Create `migrations/003_initial_settings.sql`
  - **Action**: Insert initial bot settings (global_average_period_days=0, admin_username='', default_title='')
  - **File**: Create `migrations/005_add_default_title_setting.sql` (if not included in 003)
  - **Action**: Ensure `default_title` setting exists in `bot_settings` table with empty string as default value
  - **File**: Update `docs/database_schema.md`
  - **Action**: Document `full_title` field in users table (admin-set base title, displayed title calculated from it)
  - **Action**: Document `default_title` setting in bot_settings table (shared base title for all new users)
  - **Action**: Document schema with table structures, relationships, and indexes
  - **Notes**: Use Supabase SQL editor or migration tool

- [ ] **Task 1.5: Supabase Connection Setup**
  - **File**: Create `src/infrastructure/database/supabase_client.py`
  - **Action**: Implement `get_supabase_client()` function using `supabase-py` with connection pooling
  - **Action**: Add retry logic with exponential backoff for connection failures
  - **File**: Create `src/infrastructure/config/settings.py`
  - **Action**: Load environment variables using `python-dotenv`, validate required variables
  - **Notes**: Handle missing credentials gracefully with clear error messages

- [ ] **Task 1.6: Domain Models**
  - **File**: Update `src/domain/entities/user.py`
  - **Action**: Add `full_title` field to `User` entity (Title value object, set by admin)
  - **Action**: Keep existing fields: `id`, `telegram_user_id`, `telegram_username`, `display_name`, `title` (displayed title, calculated from full_title), `title_letter_count`, `title_locked`, `timezone`, `language`, `last_percentage`, `last_processed_date`, `created_at`, `updated_at`
  - **Action**: Add `set_full_title(full_title: Title)` method to User entity
  - **File**: Update `src/domain/value_objects/title.py`
  - **Action**: Keep `letter_count()` method (exclude spaces, alphanumeric only)
  - **Action**: Add `substring_by_letter_count(count: int) -> Title` method to extract substring preserving structure (spaces, punctuation)
  - **File**: Create `src/domain/value_objects/percentage.py`
  - **Action**: Define `Percentage` value object with validation (0-100 range)
  - **File**: Create `src/domain/value_objects/timezone.py`
  - **Action**: Define `Timezone` value object with validation using `pytz`
  - **File**: Create `src/domain/exceptions.py`
  - **Action**: Define custom exception hierarchy: `DomainError`, `TitleLockedError`, `InvalidPercentageError`, `UserNotFoundError`, `InvalidTimezoneError`
  - **Notes**: Use dataclasses or Pydantic models for entities, immutable value objects

**Phase 2: Repository Layer (Week 1-2)**

- [ ] **Task 2.1: User Repository Interface**
  - **File**: Create `src/domain/repositories/user_repository.py`
  - **Action**: Define abstract `IUserRepository` interface with methods: `get_by_telegram_id()`, `get_by_username()`, `save()`, `find_all()`, `find_by_title_letter_count_range()`, `count_active_users()`
  - **Notes**: Use `abc.ABC` and `@abstractmethod` decorators

- [ ] **Task 2.2: User Repository Implementation**
  - **File**: Create `src/infrastructure/database/repositories/supabase_user_repository.py`
  - **Action**: Implement `SupabaseUserRepository` class implementing `IUserRepository`
  - **Action**: Use `supabase-py` client for database operations, handle SQL injection with parameterized queries
  - **File**: Create `tests/integration/test_supabase_user_repository.py`
  - **Action**: Integration tests with test database (use fixtures to reset database)
  - **Notes**: Handle connection errors, return None if user not found

- [ ] **Task 2.3: Statistics Repository Interface and Implementation**
  - **File**: Create `src/domain/repositories/statistics_repository.py`
  - **Action**: Define abstract `IStatisticsRepository` interface
  - **File**: Create `src/infrastructure/database/repositories/supabase_statistics_repository.py`
  - **Action**: Implement methods: `create_daily_snapshot()`, `get_snapshots_by_period()`, `get_global_average()`, `cache_statistics()`, `get_cached_statistics()`, `is_cache_valid()`
  - **Notes**: Use database transactions for snapshot creation

- [ ] **Task 2.4: Title History Repository**
  - **File**: Create `src/domain/repositories/title_history_repository.py`
  - **Action**: Define abstract `ITitleHistoryRepository` interface
  - **File**: Create `src/infrastructure/database/repositories/supabase_title_history_repository.py`
  - **Action**: Implement methods: `save()`, `get_by_user()`, `get_recent()`
  - **Notes**: Store full history for statistics analysis

- [ ] **Task 2.5: Settings Repository**
  - **File**: Create `src/domain/repositories/settings_repository.py`
  - **Action**: Define abstract `ISettingsRepository` interface with methods: `get()`, `set()`, `get_global_average_period()`, `set_global_average_period()`, `get_default_title()`, `set_default_title()`
  - **File**: Create `src/infrastructure/database/repositories/supabase_settings_repository.py`
  - **Action**: Implement methods: `get()`, `set()`, `get_global_average_period()`, `set_global_average_period()`, `get_default_title()`, `set_default_title()`
  - **Action**: `get_default_title()` returns default title from `bot_settings` table (key: 'default_title'), returns empty string if not set
  - **Action**: `set_default_title(title: str)` validates title (max 500 chars, no control characters) before updating `bot_settings.default_title` setting, raises `ValueError` if invalid
  - **Notes**: Cache settings in memory for performance, refresh periodically

- [ ] **Task 2.6: Telegram User Resolver Service (Infrastructure)**
  - **File**: Create `src/infrastructure/telegram/telegram_user_resolver.py`
  - **Action**: Implement `TelegramUserResolver` class with `__init__(bot_instance)` constructor (stores bot_instance internally)
  - **Action**: Implement `resolve_username_to_user_id(username: str, chat_id: int)` method (NO bot_instance parameter - uses stored instance)
  - **Action**: Uses `self.bot_instance.get_chat_member(chat_id, username)` API to resolve username to user_id (returns ChatMember object with user.user_id)
  - **Note**: Telegram Bot API limitation: Username resolution requires chat_id context - cannot resolve username to user_id without chat context
  - **Action**: Returns `telegram_user_id` (int) or raises `UserNotFoundError` if username doesn't exist in chat
  - **Action**: Handles Telegram API errors gracefully (network errors, rate limits)
  - **File**: Create `tests/unit/test_telegram_user_resolver.py`
  - **Action**: Unit tests with mocked bot instance, test successful resolution, test user not found, test API errors
  - **Notes**: This service belongs in infrastructure layer to maintain Clean Architecture. Resolver is initialized once in main.py with bot_instance and injected into use cases (not created per-request).

**Phase 3: Application Layer (Week 2-3)**

- [ ] **Task 3.1: Message Parsing Service**
  - **File**: Create `src/application/services/message_parser.py`
  - **Action**: Implement `MessageParser` class with `should_process_message()` method (check `message.from_user.username == "HowGayBot"`)
  - **Action**: Implement `extract_percentage()` method using regex `r"I am (\d+)% gay!"`, validate 0-100 range, raise `InvalidPercentageError` if invalid
  - **File**: Create `tests/unit/test_message_parser.py`
  - **Action**: Unit tests for valid/invalid messages, edge cases (negative, >100, malformed)

- [ ] **Task 3.2: Title Calculation Service**
  - **File**: Update `src/domain/services/title_calculation_service.py`
  - **Action**: Refactor `TitleCalculationService` with `calculate_displayed_title(full_title: Title, percentage: Percentage)` method
  - **Action**: Implement full_title substring strategy based on percentage rules:
    - 0% → Return substring with first 3 letters from full_title
    - 1-5% → Return substring with first 1 letter from full_title
    - 95-99% → Return substring with (full_title_letters - 1) letters from full_title
    - 100% → Return substring with (full_title_letters - active_user_count) letters from full_title
  - **Action**: Use `Title.substring_by_letter_count()` method to extract substring preserving structure
  - **Action**: Handle edge case: if full_title is empty, return empty Title
  - **Action**: Handle edge case: if calculated letter count < 0, return empty Title
  - **File**: Update `tests/unit/test_title_calculation_service.py`
  - **Action**: Unit tests for all percentage ranges, edge cases (empty full_title, negative count, full_title structure preservation)

- [ ] **Task 3.3: Update Title Use Case**
  - **File**: Update `src/application/use_cases/update_title_use_case.py`
  - **Action**: Update `UpdateTitleUseCase.execute()` to use `user.full_title` instead of `user.title`
  - **Action**: Check if full_title is set (if empty, log warning and skip title update)
  - **Action**: Check if title is locked (raise `TitleLockedError` if locked and not admin manual update)
  - **Action**: Check if first message today (timezone-aware date comparison using `pytz`)
  - **Action**: Calculate displayed title from full_title using `TitleCalculationService.calculate_displayed_title(full_title, percentage)`
  - **Action**: Update displayed title (not full_title), save user, create title history entry, create daily snapshot if first message of day
  - **Action**: Use database transaction (wrap all operations)
  - **File**: Update `tests/unit/test_update_title_use_case.py`
  - **Action**: Unit tests with mocked dependencies, test locked title, timezone boundaries, empty full_title, full_title preservation

- [ ] **Task 3.4: Get Leaderboard Use Case**
  - **File**: Create `src/application/use_cases/get_leaderboard_use_case.py`
  - **Action**: Implement `GetLeaderboardUseCase` class with `execute(limit, offset, sort_order)` method
  - **Action**: Sort users by `title_letter_count` (ascending or descending)
  - **Action**: Support pagination with limit/offset
  - **Action**: Return user position in leaderboard
  - **Notes**: Use database ORDER BY for efficient sorting

- [ ] **Task 3.5: Get User Stats Use Case**
  - **File**: Create `src/application/use_cases/get_user_stats_use_case.py`
  - **Action**: Implement `GetUserStatsUseCase` class with `execute(user_id)` method
  - **Action**: Return user current title, percentage, position in leaderboard
  - **Action**: Get recent title changes (last 3-5 entries from title_history)
  - **Action**: Get daily/weekly/monthly trends from daily_snapshots
  - **Notes**: Aggregate trends efficiently from snapshots

- [ ] **Task 3.6: Calculate Statistics Use Case**
  - **File**: Create `src/application/use_cases/calculate_statistics_use_case.py`
  - **Action**: Implement `CalculateStatisticsUseCase` class with `execute(period_days=None)` method
  - **Action**: Check cache first (if valid, return cached value)
  - **Action**: Calculate global average for configured period (get from settings, default 0 = all-time)
  - **Action**: Store in cache with expiration (e.g., +1 day)
  - **Action**: Batch calculation for performance (aggregate from daily_snapshots)
  - **Notes**: Use database aggregation (AVG, COUNT) for efficient calculation

- [ ] **Task 3.7: Create User Use Cases (User Registration)**
  - **File**: Create `src/application/use_cases/register_user_use_case.py` (Note: Also known as CreateUserUseCase - used for both user registration and admin adding users internally)
  - **Action**: Implement `RegisterUserUseCase` class with `execute(telegram_user_id: int, telegram_username: Optional[str], display_name: Optional[str])` method
  - **Note**: Parameters are extracted from `update.message.from_user` in the handler (telegram_user_id from `from_user.id`, telegram_username from `from_user.username`, display_name from `from_user.full_name`)
  - **Action**: Validate inputs: telegram_user_id must be > 0, telegram_username and display_name can be None
  - **Action**: Check if user already exists (if exists, return success - idempotent)
  - **Action**: Get default title from settings repository (`get_default_title()`)
  - **Action**: Create new user with default title as `full_title`, `title` (displayed) starts as empty string
  - **Action**: Set user language to 'en' (default), timezone to 'UTC' (default)
  - **Action**: Save user to repository (wrap in try/except for database errors)
  - **Action**: Handle errors: Database connection failures, settings retrieval failures, invalid telegram_user_id
  - **Action**: Return success message indicating registration status or raise appropriate exception
  - **File**: Create `tests/unit/test_register_user_use_case.py`
  - **Action**: Unit tests with mocked dependencies, test existing user (idempotent), test default title assignment, test empty default title, test database errors, test invalid inputs

- [ ] **Task 3.8: Admin Commands Use Cases**
  - **File**: Create `src/application/use_cases/set_full_title_use_case.py`
  - **Action**: Implement `SetFullTitleUseCase` class with `execute(user_id, full_title: str, admin_username)` method
  - **Action**: Validate admin, get user by user_id, set full_title, recalculate displayed title from full_title with current percentage (if exists), save user
  - **File**: Create `src/application/use_cases/lock_title_use_case.py`
  - **Action**: Implement `LockTitleUseCase` class with `execute(user_id, admin_username)` method, validate admin, set `title_locked=True`
  - **File**: Create `src/application/use_cases/unlock_title_use_case.py`
  - **Action**: Implement `UnlockTitleUseCase` class with `execute(user_id, admin_username)` method, validate admin, set `title_locked=False`
  - **File**: Create `src/application/use_cases/set_global_average_period_use_case.py`
  - **Action**: Implement `SetGlobalAveragePeriodUseCase` class with `execute(period_days, admin_username)` method, validate admin, update bot_settings
  - **File**: Create `src/application/use_cases/add_user_use_case.py`
  - **Action**: Implement `AddUserUseCase` class with `__init__(telegram_user_resolver, register_user_use_case, settings_repository, admin_service)` constructor (inject dependencies)
  - **Action**: Implement `execute(username: str, chat_id: int, admin_user_id: int, admin_username: str)` method (NO telegram_user_resolver parameter - injected in constructor)
  - **Note**: Dependencies (telegram_user_resolver, register_user_use_case) are injected via constructor to maintain Clean Architecture (use case doesn't depend on bot_instance directly)
  - **Action**: Validate admin (validate admin_user_id and admin_username)
  - **Action**: Validate inputs: username must not be empty, chat_id must be valid integer
  - **Action**: Resolve username to Telegram user ID using `telegram_user_resolver.resolve_username_to_user_id(username, chat_id)` (resolver uses stored bot_instance internally, no need to pass it)
  - **Action**: If username doesn't exist in Telegram chat, raise `UserNotFoundError` with friendly message
  - **Action**: If resolution fails (network error, API error), raise `ValueError` with context
  - **Action**: If user already exists in database (by telegram_user_id), return success (idempotent)
  - **Action**: Get user display_name from Telegram API (ChatMember object contains user.full_name) if available, otherwise use None
  - **Action**: Call `register_user_use_case.execute(telegram_user_id, username, display_name)` to create user (avoids code duplication - RegisterUserUseCase handles default title and user creation logic)
  - **Action**: If RegisterUserUseCase raises exception, handle and re-raise with context (wrap in try/except, log error, re-raise with friendly message)
  - **Note**: AddUserUseCase delegates user creation to RegisterUserUseCase to avoid duplicating logic (both `/register` and `/add_user` use same core user creation logic)
  - **Action**: Handle errors: Database connection failures, settings retrieval failures, resolver failures
  - **File**: Create `tests/unit/test_add_user_use_case.py`
  - **Action**: Unit tests with mocked telegram_user_resolver, test username resolution, test existing user (idempotent), test user not found, test resolver errors
  - **File**: Create `src/application/use_cases/set_default_title_use_case.py`
  - **Action**: Implement `SetDefaultTitleUseCase` class with `execute(default_title: str, admin_user_id: int, admin_username: str)` method
  - **Action**: Validate admin (validate admin_user_id and admin_username)
  - **Action**: Validate default_title: max length 500 characters, no control characters (allow newlines/spaces), trim whitespace
  - **Action**: If validation fails, raise `ValueError` with specific message (e.g., "Title too long (max 500 characters)" or "Title contains invalid characters")
  - **Action**: Update `bot_settings.default_title` using settings repository (repository validates again, but use case validates first)
  - **Action**: Existing users are NOT updated automatically (they keep their current `full_title`)
  - **Action**: Only new registrations will use the new default title
  - **Action**: Return success message with new default title
  - **File**: Create `src/application/use_cases/migrate_users_to_default_title_use_case.py`
  - **Action**: Implement `MigrateUsersToDefaultTitleUseCase` class with `execute(admin_user_id: int, admin_username: str, user_repository, settings_repository, title_calculation_service)` method
  - **Action**: Validate admin, get default title from settings (if empty, raise ValueError)
  - **Action**: Update all existing users' `full_title` to current default title (batch update)
  - **Action**: Recalculate displayed titles for all users (if they have percentage) using title_calculation_service
  - **Action**: Return count of users updated
  - **File**: Create `tests/unit/test_set_default_title_use_case.py`
  - **Action**: Unit tests with mocked dependencies, test admin validation, test settings update, test validation failures (too long, invalid chars)
  - **File**: Create `tests/unit/test_migrate_users_to_default_title_use_case.py`
  - **Action**: Unit tests with mocked dependencies, test admin validation, test batch update, test empty default title error
  - **File**: Create `src/application/use_cases/manual_recheck_use_case.py`
  - **Action**: Implement `ManualRecheckUseCase` class with `execute(admin_username, days=7, target_username=None)` method, process missed messages from last N days
  - **Notes**: All admin use cases validate admin username from env var

**Phase 4: Presentation Layer (Week 3-4)**

- [ ] **Task 4.1: Command Handlers**
  - **File**: Update `src/presentation/handlers/command_handlers.py`
  - **Action**: Implement `/me` handler - call `GetUserStatsUseCase`, format response with inline keyboard
  - **Action**: Implement `/who @username` handler - get user by username, call `GetUserStatsUseCase`
  - **Action**: Implement `/leaderboard` handler - call `GetLeaderboardUseCase`, format as numbered list
  - **Action**: Implement `/stats [range]` handler - call `CalculateStatisticsUseCase`, show global average and user stats
  - **Action**: Implement `/register` handler - extract user info from `update.message.from_user` (id, username, full_name), call `RegisterUserUseCase`, show success message with welcome text, handle errors gracefully
  - **Action**: Update `/start` handler - show welcome message, optionally mention `/register` command for registration
  - **Action**: Implement `/add_user @username <chat_id>` handler (admin only) - extract username and chat_id from command args, call `AddUserUseCase` (passing telegram_user_resolver from dependency injection - created in main.py, not per-request), show success or error message
  - **Note**: TelegramUserResolver is a singleton service created once in main.py and injected into all handlers/use cases that need it, not created per-request
  - **Action**: Implement `/set_default_title <title>` handler (admin only) - extract title from command args (join remaining args), call `SetDefaultTitleUseCase`, show confirmation message or validation error
  - **Action**: Implement `/migrate_users_to_default_title` handler (admin only) - call `MigrateUsersToDefaultTitleUseCase`, show count of users updated
  - **Action**: Add rate limiting (optional - use python-telegram-bot's rate limiting or manual tracking): Limit `/register` to once per user per minute to prevent spam
  - **Action**: Implement `/set_full_title @username <full_title>` handler (admin only) - call `SetFullTitleUseCase`
  - **Action**: Implement `/lock_title @username` handler (admin only) - call `LockTitleUseCase`
  - **Action**: Implement `/unlock_title @username` handler (admin only) - call `UnlockTitleUseCase`
  - **Action**: Implement `/set_global_average_period <days>` handler (admin only) - call `SetGlobalAveragePeriodUseCase`
  - **Action**: Implement `/recheck_messages [@username] [--days N]` handler (admin only) - call `ManualRecheckUseCase`
  - **Action**: Implement `/help` handler - show usage guidelines with language support, include `/register` command
  - **Notes**: Handle errors gracefully, show user-friendly messages

- [ ] **Task 4.2: Inline Keyboard Builder**
  - **File**: Create `src/presentation/keyboards/inline_keyboard_builder.py`
  - **Action**: Implement `InlineKeyboardBuilder` class with `build_main_keyboard(is_admin=False)` method
  - **Action**: Create buttons: "📊 My Stats", "👥 Leaderboard", "📝 Help"
  - **Action**: If admin, add: "⚙️ Settings", "🔒 Lock Title"
  - **Notes**: Use `InlineKeyboardMarkup` from python-telegram-bot

- [ ] **Task 4.3: Inline Query Handler**
  - **File**: Create `src/presentation/handlers/inline_query_handler.py`
  - **Action**: Handle inline query when user types `@BotName`
  - **Action**: Show inline keyboard using `InlineKeyboardBuilder`
  - **Action**: Check if user is admin (compare username with env var)

- [ ] **Task 4.4: Message Monitoring Handler**
  - **File**: Create `src/presentation/handlers/message_handler.py`
  - **Action**: Implement message handler that filters messages from @HowGayBot
  - **Action**: Use `MessageParser` to extract percentage
  - **Action**: Extract username of user who received message (from message context/reply)
  - **Action**: Call `UpdateTitleUseCase` if first message today
  - **Action**: Error handling and logging (log skipped messages, errors)
  - **Notes**: Handle group messages where bot needs to identify recipient

- [ ] **Task 4.5: Chat Member Handler (Group Events)**
  - **File**: Create `src/presentation/handlers/chat_member_handler.py`
  - **Action**: Implement handler for `MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS)` to detect when bot is added to group
  - **Action**: Check if bot itself is in `new_chat_members` list (when bot is added to group) - compare `member.id` with `context.bot.id`
  - **Action**: When bot is added to group: Send welcome message explaining registration process and `/register` command
  - **Action**: Handle both group chats and supergroups (same logic applies)
  - **Action**: Note: Private chats don't trigger `NEW_CHAT_MEMBERS` - users can still use `/register` directly in private chat, no special handling needed
  - **Action**: Optional: Use `ChatMemberUpdated` handler for more detailed bot membership tracking (future enhancement)
  - **Action**: Error handling and logging (handle message send failures, permission errors)
  - **File**: Update `src/presentation/main.py`
  - **Action**: Register `MessageHandler` with `filters.StatusUpdate.NEW_CHAT_MEMBERS` filter separately for bot-added-to-group events (distinct from message monitoring handler)
  - **Notes**: Welcome message should explain how users can register via `/register` command. Handler only triggers for groups, not private chats.

- [ ] **Task 4.6: Callback Query Handler**
  - **File**: Create `src/presentation/handlers/callback_query_handler.py`
  - **Action**: Handle inline button clicks (callback_data: "me", "leaderboard", "help", "settings", "lock_title")
  - **Action**: Route to appropriate use cases or handlers
  - **Action**: Update message or send new message based on button clicked
  - **Notes**: Use `query.answer()` and `query.message.edit_text()` or `reply_text()`

- [ ] **Task 4.7: Localization System**
  - **File**: Create `src/infrastructure/i18n/translations.py`
  - **Action**: Define translation dictionaries for English and Russian
  - **Action**: Implement `translate(key, language)` function
  - **Action**: Create `get_user_language(user_id)` function (get from database)
  - **File**: Create `src/presentation/utils/localization.py`
  - **Action**: Helper function to get translated message based on user's language preference
  - **Notes**: Use simple dict-based approach initially, can upgrade to i18n library later

- [ ] **Task 4.8: Application Entry Point**
  - **File**: Create `src/presentation/main.py`
  - **Action**: Replace `bot.py` - create Telegram application using `ApplicationBuilder`
  - **Action**: Initialize repositories, use cases, services with dependency injection
  - **Action**: Create TelegramUserResolver instance once: `telegram_user_resolver = TelegramUserResolver(bot_instance=app.bot)` (app.bot is available after `ApplicationBuilder().build()`, or access via `context.bot` if needed)
  - **Note**: Resolver must be created AFTER `app.bot` is available (after `ApplicationBuilder().build()` or `app.initialize()`), but BEFORE use cases are instantiated
  - **Action**: Pass TelegramUserResolver to AddUserUseCase and any other use cases/handlers that need it
  - **Action**: Register all handlers (handlers receive dependencies via constructor):
    - CommandHandler for all commands (`/start`, `/me`, `/register`, `/add_user`, `/set_default_title`, `/migrate_users_to_default_title`, etc.)
    - CallbackQueryHandler for inline button clicks
    - MessageHandler with `filters.TEXT & (~filters.COMMAND)` for message monitoring (filters @HowGayBot messages)
    - MessageHandler with `filters.StatusUpdate.NEW_CHAT_MEMBERS` for bot-added-to-group events (distinct handler from message monitoring)
    - InlineQueryHandler for @BotName queries
  - **Action**: Start bot with `app.run_polling()` or `app.run_webhook()` for production
  - **Notes**: Use manual dependency injection (pass dependencies to handlers). TelegramUserResolver is created ONCE in main.py (singleton pattern) with bot_instance and injected into use cases/handlers. Do NOT create resolver per-request.

**Phase 5: Migration (Week 4)**

- [ ] **Task 5.1: Google Sheets Export Script**
  - **File**: Create `scripts/export_google_sheets.py`
  - **Action**: Read from Google Sheets using existing `gspread` credentials
  - **Action**: Export to CSV format with columns: `name`, `tg_name`, `title`, `letters`
  - **Action**: Validate data structure, handle missing columns
  - **Action**: Save to `migrations/google_sheets_export.csv`
  - **Notes**: Can be run standalone before migration

- [ ] **Task 5.2: Migration Script**
  - **File**: Create `migrations/002_migrate_google_sheets.py`
  - **Action**: Implement `--dry-run` mode (preview changes without executing)
  - **Action**: Implement `--execute` mode (perform migration)
  - **Action**: Implement `--rollback` mode (revert migration)
  - **Action**: For each row: fetch `telegram_user_id` from Telegram API using username
  - **Action**: If username doesn't exist in Telegram → skip with warning, log for manual intervention
  - **Action**: Create user record in database with migrated data
  - **Action**: Calculate `title_letter_count` from title
  - **Action**: Create initial daily snapshot if date information available
  - **Action**: Validate migration (count records, sample checks)
  - **Notes**: Use argparse for CLI arguments, provide progress feedback

- [ ] **Task 5.3: Migration Testing**
  - **File**: Create `tests/integration/test_migration.py`
  - **Action**: Test with sample CSV data
  - **Action**: Test username → user_id resolution
  - **Action**: Test rollback functionality
  - **Action**: Validate migrated data integrity
  - **Notes**: Use test database for migration testing

**Phase 6: Statistics & Background Jobs (Week 4-5)**

- [ ] **Task 6.1: Daily Snapshot Job**
  - **File**: Create `src/infrastructure/jobs/daily_snapshot_job.py`
  - **Action**: Implement `create_daily_snapshots()` function
  - **Action**: Run at midnight UTC (or configurable timezone)
  - **Action**: Create snapshot for all users who had activity that day
  - **Action**: Handle timezone-aware date calculations using `pytz`
  - **Action**: Error handling and logging (log failures, retry logic)
  - **Notes**: Use APScheduler for scheduling

- [ ] **Task 6.2: Statistics Calculation Job**
  - **File**: Create `src/infrastructure/jobs/statistics_calculation_job.py`
  - **Action**: Implement `calculate_and_cache_statistics()` function
  - **Action**: Calculate global average for configured period
  - **Action**: Update cache with expiration (e.g., +1 day)
  - **Action**: Batch processing for performance (aggregate from daily_snapshots)
  - **Action**: Handle cache expiration checks
  - **Notes**: Run periodically (e.g., every hour) to keep cache fresh

- [ ] **Task 6.3: Job Scheduler Setup**
  - **File**: Create `src/infrastructure/jobs/scheduler.py`
  - **Action**: Initialize APScheduler with async support
  - **Action**: Configure daily snapshot job (midnight UTC)
  - **Action**: Configure statistics calculation job (every hour or configurable)
  - **Action**: Integrate with Telegram application lifecycle (start/stop with bot)
  - **Notes**: Use `AsyncIOScheduler` for async compatibility

**Phase 7: Error Handling & Logging (Week 5)**

- [ ] **Task 7.1: Error Handling**
  - **File**: Update `src/domain/exceptions.py`
  - **Action**: Ensure all custom exceptions inherit from `DomainError`
  - **File**: Create `src/presentation/errors/error_handler.py`
  - **Action**: Implement global error handler for Telegram updates
  - **Action**: Map domain exceptions to user-friendly messages
  - **Action**: Log errors with structured logging
  - **Action**: Send error notifications to admin on critical failures
  - **Notes**: Use try/except blocks in all handlers

- [ ] **Task 7.2: Logging Infrastructure**
  - **File**: Create `src/infrastructure/logging/logger.py`
  - **Action**: Configure `structlog` or `loguru` for structured logging
  - **Action**: Set log levels: DEBUG, INFO, WARNING, ERROR
  - **Action**: Log to both file (`logs/bot.log`) and console (stdout for Railway)
  - **Action**: Add request ID tracking for correlation
  - **Action**: Log all title changes, admin actions, errors
  - **Notes**: Use JSON format for structured logs, include timestamps, user context

**Phase 8: Testing (Week 5-6)**

- [ ] **Task 8.1: Unit Tests**
  - **Files**: Create `tests/unit/test_*.py` for all domain models, use cases, services
  - **Action**: Test all domain entities and value objects (User, Title, Percentage, Timezone)
  - **Action**: Test all use cases with mocked dependencies (UpdateTitleUseCase, GetLeaderboardUseCase, etc.)
  - **Action**: Test all services (MessageParser, TitleCalculationService)
  - **Action**: Test edge cases: Invalid percentages, locked titles, timezone boundaries
  - **Action**: Target 80%+ code coverage (use `pytest-cov`)
  - **File**: Create `pytest.ini`
  - **Action**: Configure pytest with async support, coverage settings
  - **File**: Create `tests/conftest.py`
  - **Action**: Define shared fixtures for mocks, test data
  - **Notes**: Use `pytest-mock` for mocking, `pytest-asyncio` for async tests

- [ ] **Task 8.2: Integration Tests**
  - **Files**: Create `tests/integration/test_*.py` for all repositories
  - **Action**: Test all repositories with test Supabase database
  - **Action**: Test database transactions
  - **Action**: Test statistics calculation with real data
  - **Action**: Test message parsing with various formats
  - **File**: Create `tests/integration/conftest.py`
  - **Action**: Set up test database fixtures (reset before each test suite)
  - **Notes**: Use separate Supabase project for testing

- [ ] **Task 8.3: E2E Tests**
  - **Files**: Create `tests/e2e/test_bot_flows.py`
  - **Action**: Test full bot interaction flows (send message → receive response)
  - **Action**: Mock Telegram API responses using `python-telegram-bot` test utilities
  - **Action**: Test complete use case flows (message → title update → statistics)
  - **Action**: Test admin commands end-to-end
  - **Notes**: Use `telegram.ext.ApplicationBuilder` with test token for E2E tests

**Phase 9: Documentation & Deployment (Week 6)**

- [ ] **Task 9.1: README**
  - **File**: Create `README.md`
  - **Action**: Document project overview, features, architecture
  - **Action**: Add setup instructions (install dependencies, configure environment variables)
  - **Action**: Add database setup instructions (run migrations)
  - **Action**: Add migration guide (Google Sheets → Supabase)
  - **Action**: Add Railway deployment guide with step-by-step instructions
  - **Action**: Add usage examples for all commands
  - **Action**: Add troubleshooting section
  - **Notes**: Use Markdown formatting, include code examples

- [ ] **Task 9.2: Railway Deployment Configuration**
  - **File**: Create `Procfile`
  - **Action**: Add command: `python -m src.presentation.main`
  - **File**: Optionally create `railway.json`
  - **Action**: Configure Railway-specific settings (if needed)
  - **File**: Update `README.md` with Railway deployment section
  - **Action**: Document how to set environment variables in Railway dashboard
  - **Action**: Document how to connect Supabase database
  - **Action**: Document health check endpoint (if implemented)
  - **Notes**: Test deployment on Railway staging environment first

- [ ] **Task 9.3: Architecture Documentation**
  - **File**: Create `docs/architecture.md`
  - **Action**: Document Clean Architecture layers and their responsibilities
  - **Action**: Document dependency flow (Presentation → Application → Domain ← Infrastructure)
  - **Action**: Include architecture diagrams (text-based or Mermaid)
  - **File**: Create `docs/database_schema.md`
  - **Action**: Document all tables, relationships, indexes, constraints
  - **Action**: Include ER diagram (text-based or Mermaid)
  - **File**: Create `docs/migration_guide.md`
  - **Action**: Step-by-step migration instructions from Google Sheets
  - **Action**: Troubleshooting common migration issues

### Acceptance Criteria

**AC1: Message Monitoring - Happy Path**
- **Given**: Message from @HowGayBot with text "I am 90% gay!" in a group where the bot is active
- **When**: Bot processes the message
- **Then**: Extract percentage 90 from message text using regex pattern
- **And**: Validate percentage is within 0-100 range (no exception raised)
- **And**: Update user title if this is the first message today (timezone-aware check)
- **And**: Create daily snapshot if first message of day

**AC2: Message Monitoring - Invalid Bot**
- **Given**: Message from @DifferentBot with text "I am 90% gay!"
- **When**: Bot processes the message
- **Then**: Message is ignored (not from @HowGayBot)
- **And**: No title update occurs
- **And**: No error is logged

**AC3: Message Monitoring - Invalid Percentage Range**
- **Given**: Message from @HowGayBot with text "I am 150% gay!" or "I am -10% gay!"
- **When**: Bot processes the message
- **Then**: `InvalidPercentageError` is raised
- **And**: Message is logged as invalid with warning level
- **And**: No title update occurs
- **And**: User receives no error message (silent failure for invalid messages)

**AC4: Title Calculation - Percentage Rules (Full Title Strategy)**
- **Given**: User with full_title "Super Gay Title" (15 letters) set by admin and percentage value from @HowGayBot
- **When**: Title is calculated based on percentage:
  - 0% → Then: Displayed title shows first 3 letters from full_title (e.g., "Sup" if full_title is "Super Gay Title")
  - 3% → Then: Displayed title shows first 1 letter from full_title (e.g., "S")
  - 97% → Then: Displayed title shows (15 - 1) = 14 letters from full_title (e.g., "Super Gay Titl")
  - 100% → Then: Displayed title shows (15 - N) letters where N = active user count
- **And**: Letter count is recalculated and cached in `title_letter_count` field
- **And**: Full title structure is preserved (spaces, punctuation maintained when extracting substring)

**AC5: Title Calculation - Edge Case Negative Length**
- **Given**: User with full_title "A" (1 letter) and percentage 100% with active user count = 5
- **When**: Title is calculated (1 - 5 = -4)
- **Then**: Displayed title is set to empty string ""
- **And**: `title_letter_count` is set to 0
- **And**: No exception is raised

**AC5.1: Title Calculation - Full Title Not Set**
- **Given**: User with no full_title set (full_title is empty or null)
- **When**: Percentage message is processed
- **Then**: Displayed title remains empty ""
- **And**: No error is raised (expected behavior - admin must set full_title first)
- **And**: Warning is logged that full_title is not set

**AC6: First Message Per Day - Different Dates**
- **Given**: User sends message from @HowGayBot at 11:59 PM on 2026-01-10 (timezone: America/New_York)
- **And**: User sends another message at 12:01 AM on 2026-01-11 (same timezone)
- **When**: Both messages are processed
- **Then**: First message is processed (2026-01-10)
- **And**: Second message is processed (2026-01-11, different calendar date)
- **And**: Both daily snapshots are created
- **And**: `last_processed_date` is updated to 2026-01-11 after second message

**AC7: First Message Per Day - Same Date**
- **Given**: User sends message from @HowGayBot at 10:00 AM on 2026-01-10
- **And**: User sends another message at 2:00 PM on 2026-01-10 (same calendar date)
- **When**: Both messages are processed
- **Then**: First message is processed and title is updated
- **And**: Second message is ignored (not first message today)
- **And**: Only one daily snapshot is created (for first message)
- **And**: `last_processed_date` remains 2026-01-10

**AC8: Title Locking - Auto-Update Prevention**
- **Given**: User with `title_locked=True` and title "LockedTitle"
- **When**: @HowGayBot sends percentage message
- **Then**: `TitleLockedError` is raised
- **And**: Title remains unchanged ("LockedTitle")
- **And**: No title history entry is created
- **And**: Error is logged with info level (expected behavior, not critical)

**AC9: Title Locking - Admin Manual Update**
- **Given**: User with `title_locked=True` and title "LockedTitle"
- **And**: Admin runs `/lock_title @username NewTitle` or admin manually updates via database
- **When**: Admin manually changes title
- **Then**: Title is updated to "NewTitle"
- **And**: Title history entry is created with `change_type='manual_admin'`
- **And**: `title_locked` remains True
- **And**: Title still prevents automatic updates

**AC10: Title Unlocking**
- **Given**: User with `title_locked=True`
- **When**: Admin runs `/unlock_title @username`
- **Then**: `title_locked` is set to False
- **And**: User receives confirmation message "✅ Title unlocked for @username. Auto-updates enabled."
- **And**: Next percentage message from @HowGayBot will update title automatically

**AC11: Admin Period Customization**
- **Given**: Admin runs `/set_global_average_period 30`
- **When**: Statistics are calculated via `/stats` command
- **Then**: Global average is calculated from last 30 days of daily snapshots
- **And**: Setting is saved in `bot_settings` table with key `global_average_period_days`
- **And**: Setting persists after bot restart (loaded from database)

**AC12: Admin Period Customization - All-Time**
- **Given**: Admin runs `/set_global_average_period 0`
- **When**: Statistics are calculated
- **Then**: Global average is calculated from all daily snapshots (all-time)
- **And**: Setting is saved with value `0` (special value for all-time)

**AC13: Letter Counting**
- **Given**: Title "Super Gay"
- **When**: Letter count is calculated using `Title.letter_count()` method
- **Then**: Returns 9 (counts only alphanumeric: S-u-p-e-r-G-a-y, excludes space)
- **And**: Result is cached in `title_letter_count` database field

**AC14: Letter Counting - With Punctuation**
- **Given**: Title "Super-Gay!" or "Super_Gay123"
- **When**: Letter count is calculated
- **Then**: Returns 9 (counts only alphanumeric, excludes hyphens, underscores, punctuation, numbers)

**AC15: Leaderboard Sorting - Ascending**
- **Given**: Users with titles: "A" (1 letter), "Super Gay" (9 letters), "Test" (4 letters)
- **When**: Leaderboard is displayed with sort_order='asc'
- **Then**: Users are ordered: "A", "Test", "Super Gay"
- **And**: Position numbers are shown (1, 2, 3)

**AC16: Leaderboard Sorting - Descending**
- **Given**: Same users as AC15
- **When**: Leaderboard is displayed with sort_order='desc'
- **Then**: Users are ordered: "Super Gay", "Test", "A"
- **And**: Position numbers are shown (1, 2, 3)

**AC17: Leaderboard Pagination**
- **Given**: 25 users in database
- **When**: Leaderboard is displayed with limit=10, offset=0
- **Then**: First 10 users are displayed
- **When**: Leaderboard is displayed with limit=10, offset=10
- **Then**: Users 11-20 are displayed

**AC18: Manual Recheck - Success**
- **Given**: Admin runs `/recheck_messages --days 7`
- **And**: There are 3 unprocessed messages from last 7 days
- **When**: Recheck is executed
- **Then**: All 3 messages are processed
- **And**: 3 titles are updated
- **And**: Admin receives message: "✅ Recheck complete! Processed: 3 messages, Updated titles: 3 users"

**AC19: Manual Recheck - Already Processed**
- **Given**: Admin runs `/recheck_messages --days 7`
- **And**: All messages from last 7 days are already processed
- **When**: Recheck is executed
- **Then**: No messages are processed
- **And**: Admin receives message: "✅ Recheck complete! Processed: 0 messages, Updated titles: 0 users, Skipped (already processed): N messages"

**AC20: Manual Recheck - Specific User**
- **Given**: Admin runs `/recheck_messages @username --days 30`
- **When**: Recheck is executed
- **Then**: Only unprocessed messages for @username from last 30 days are checked
- **And**: Other users are not affected

**AC21: User Stats - Current Stats**
- **Given**: User runs `/me` command
- **When**: User stats are retrieved
- **Then**: Display current title, current percentage, position in leaderboard
- **And**: Show recent title changes (last 3-5 entries)
- **And**: Response includes inline keyboard with "📊 My Stats", "👥 Leaderboard", "📝 Help"

**AC22: User Stats - Trends**
- **Given**: User runs `/stats` command
- **When**: User stats with trends are retrieved
- **Then**: Display daily/weekly/monthly percentage trends
- **And**: Display global average for configured period
- **And**: Format trends in readable format (e.g., "Daily: 45%, Weekly: 42%, Monthly: 38%")

**AC23: Inline Keyboard - Regular User**
- **Given**: User types `@BotName` in chat
- **When**: Bot shows inline keyboard
- **Then**: Buttons displayed: "📊 My Stats", "👥 Leaderboard", "📝 Help"
- **And**: Admin-only buttons are NOT displayed

**AC24: Inline Keyboard - Admin User**
- **Given**: Admin user types `@BotName` in chat
- **And**: Admin username matches `ADMIN_USERNAME` env var
- **When**: Bot shows inline keyboard
- **Then**: All regular buttons are displayed
- **And**: Admin buttons are displayed: "⚙️ Settings", "🔒 Lock Title"

**AC25: Localization - English**
- **Given**: User with `language='en'` in database
- **When**: Bot sends message to user
- **Then**: Message is in English
- **And**: All command responses are in English

**AC26: Localization - Russian**
- **Given**: User with `language='ru'` in database
- **When**: Bot sends message to user
- **Then**: Message is in Russian
- **And**: All command responses are in Russian
- **Note**: Russian translations must be provided for all messages

**AC27: Error Handling - User Not Found**
- **Given**: User runs `/who @nonexistent_user`
- **When**: User lookup fails
- **Then**: `UserNotFoundError` is raised
- **And**: User receives friendly message: "User @nonexistent_user not found"
- **And**: Error is logged with warning level

**AC28: Error Handling - Admin Permission Denied**
- **Given**: Non-admin user runs `/lock_title @username`
- **When**: Admin check fails (username != ADMIN_USERNAME)
- **Then**: User receives message: "❌ Permission denied. Admin access required."
- **And**: Command is not executed
- **And**: Action is logged with warning level

**AC29: Database Transaction - Title Update Rollback**
- **Given**: Title update operation starts
- **And**: Database error occurs during title history insertion
- **When**: Transaction fails
- **Then**: All database changes are rolled back
- **And**: User title remains unchanged
- **And**: Error is logged with error level
- **And**: User receives generic error message (don't expose database errors)

**AC30: Statistics Cache - Valid Cache**
- **Given**: Statistics cache exists with valid expiration (not expired)
- **When**: Statistics are requested via `/stats`
- **Then**: Cached value is returned immediately
- **And**: No database query is executed
- **And**: Response time is fast (< 100ms)

**AC31: Statistics Cache - Expired Cache**
- **Given**: Statistics cache exists but is expired
- **When**: Statistics are requested via `/stats`
- **Then**: New calculation is performed
- **And**: Cache is updated with new value and new expiration
- **And**: Calculated value is returned

**AC32: Daily Snapshot Job - Scheduled Execution**
- **Given**: Scheduled job is configured to run at midnight UTC
- **When**: Job executes at midnight
- **Then**: Daily snapshots are created for all users who had activity that day
- **And**: Snapshots include: user_id, snapshot_date, percentage, title, title_letter_count
- **And**: Job logs execution summary (e.g., "Created 15 daily snapshots")

**AC33: Migration - Dry Run**
- **Given**: Google Sheets export CSV file exists
- **When**: Migration script runs with `--dry-run` flag
- **Then**: Preview of changes is displayed (users to migrate, usernames to resolve, etc.)
- **And**: No database changes are made
- **And**: User can review before executing

**AC34: Migration - Execute**
- **Given**: Migration dry run completed successfully
- **When**: Migration script runs with `--execute` flag
- **Then**: All users from CSV are migrated to database
- **And**: Usernames are resolved to telegram_user_id via Telegram API
- **And**: Titles and letter counts are migrated correctly
- **And**: Migration summary is displayed (successful, skipped, errors)

**AC35: User Registration - Happy Path**
- **Given**: User runs `/register` command and default title is set in bot settings (e.g., "Super Gay Title")
- **When**: Registration is processed
- **Then**: User is created in database with default title as `full_title`
- **And**: Displayed title (`title`) is empty string initially
- **And**: User receives success message: "✅ Registration successful! Your default title is set. Use /me to check your stats."
- **And**: User language is set to 'en' (default), timezone to 'UTC' (default)

**AC36: User Registration - Already Registered (Idempotent)**
- **Given**: User is already registered in database
- **When**: User runs `/register` command again
- **Then**: Registration returns success message (idempotent - no error)
- **And**: User's existing data is not modified
- **And**: Message: "✅ You're already registered! Use /me to check your stats."

**AC37: User Registration - No Default Title Set**
- **Given**: Default title is not set (empty string in bot_settings)
- **When**: User runs `/register` command
- **Then**: User is created with empty `full_title` and empty `title`
- **And**: User receives success message with note: "✅ Registration successful! Note: Default title not set by admin yet."
- **And**: User can still use bot, but title updates won't work until admin sets their `full_title` manually

**AC38: Admin Add User - Happy Path**
- **Given**: Admin runs `/add_user @username <chat_id>` and default title is set in bot settings
- **And**: Username exists in Telegram chat (identified by chat_id) and is not already in database
- **When**: Admin command is processed
- **Then**: Username is resolved to Telegram user ID via TelegramUserResolver service (uses Bot API internally)
- **And**: User is created with default title as `full_title`
- **And**: Admin receives success message: "✅ User @username added successfully!"
- **And**: New user receives no notification (admin action only)

**AC38.1: Admin Add User - Missing Chat ID**
- **Given**: Admin runs `/add_user @username` without chat_id argument
- **When**: Command is processed
- **Then**: Admin receives error message: "❌ Usage: /add_user @username <chat_id>. Chat ID is required because Telegram API cannot resolve username without chat context."
- **And**: No user is created

**AC39: Admin Add User - Username Not Found in Telegram**
- **Given**: Admin runs `/add_user @nonexistent_user <chat_id>`
- **When**: TelegramUserResolver fails to resolve username (user doesn't exist in Telegram chat)
- **Then**: `UserNotFoundError` is raised with friendly message
- **And**: Admin receives error message: "❌ User @nonexistent_user not found in Telegram chat. Please check the username and chat_id."
- **And**: No database changes are made

**AC39.1: Admin Add User - Resolver Error**
- **Given**: Admin runs `/add_user @username <chat_id>`
- **When**: TelegramUserResolver fails due to network error or API error (not user not found)
- **Then**: `ValueError` is raised with context
- **And**: Admin receives error message: "❌ Error resolving username: [error details]"
- **And**: Error is logged with error level

**AC40: Admin Add User - User Already Exists (Idempotent)**
- **Given**: User already exists in database
- **When**: Admin runs `/add_user @existing_user <chat_id>`
- **Then**: Command returns success (idempotent - no error)
- **And**: User's existing data is not modified
- **And**: Admin receives message: "✅ User @existing_user is already registered."

**AC41: Admin Set Default Title - Happy Path**
- **Given**: Admin runs `/set_default_title Super Gay Title`
- **When**: Command is processed
- **Then**: Title is validated (max 500 chars, no control characters)
- **And**: `bot_settings.default_title` is updated to "Super Gay Title"
- **And**: Existing users' `full_title` values are NOT changed (they keep their current titles)
- **And**: Admin receives confirmation: "✅ Default title updated to 'Super Gay Title'. New registrations will use this title."
- **And**: Next new registration will use "Super Gay Title" as `full_title`

**AC41.1: Admin Set Default Title - Validation Failure (Too Long)**
- **Given**: Admin runs `/set_default_title <title_with_501_chars>`
- **When**: Command is processed
- **Then**: `ValueError` is raised with message: "Title too long (max 500 characters)"
- **And**: Admin receives error message: "❌ Title too long (max 500 characters)"
- **And**: Setting is not updated

**AC41.2: Admin Set Default Title - Validation Failure (Invalid Characters)**
- **Given**: Admin runs `/set_default_title Title\x00With\x01Control\x02Chars`
- **When**: Command is processed
- **Then**: `ValueError` is raised with message: "Title contains invalid characters"
- **And**: Admin receives error message: "❌ Title contains invalid characters (control characters not allowed)"
- **And**: Setting is not updated

**AC42: Admin Set Default Title - Empty Title**
- **Given**: Admin runs `/set_default_title` with empty string or no argument
- **When**: Command is processed
- **Then**: `bot_settings.default_title` is set to empty string
- **And**: Admin receives confirmation: "✅ Default title cleared. New registrations will have no default title."
- **And**: Future registrations will have empty `full_title`

**AC43: Admin Set Default Title - Permission Denied**
- **Given**: Non-admin user runs `/set_default_title Some Title`
- **When**: Admin check fails
- **Then**: User receives message: "❌ Permission denied. Admin access required."
- **And**: Setting is not updated
- **And**: Action is logged with warning level

**AC43.1: Admin Migrate Users to Default Title - Happy Path**
- **Given**: Admin runs `/migrate_users_to_default_title` and default title is set (e.g., "New Title")
- **And**: There are 10 existing users in database
- **When**: Command is processed
- **Then**: All 10 users' `full_title` is updated to "New Title"
- **And**: Displayed titles are recalculated for users who have percentage values
- **And**: Admin receives confirmation: "✅ Migrated 10 users to default title 'New Title'"

**AC43.2: Admin Migrate Users to Default Title - Empty Default Title**
- **Given**: Default title is not set (empty string)
- **When**: Admin runs `/migrate_users_to_default_title`
- **Then**: `ValueError` is raised: "Default title is not set"
- **And**: Admin receives error message: "❌ Cannot migrate: Default title is not set. Use /set_default_title first."
- **And**: No users are updated

**AC44: Registration Error Handling - Database Failure**
- **Given**: User runs `/register` command
- **When**: Database connection fails during registration
- **Then**: `ConnectionError` or database-specific exception is raised
- **And**: User receives friendly error message: "❌ Registration failed due to a temporary issue. Please try again later."
- **And**: Error is logged with error level (don't expose database errors to user)

**AC45: Bot Added to Group - Welcome Message**
- **Given**: Bot is added to a Telegram group
- **When**: Bot detects it was added (via `NEW_CHAT_MEMBERS` filter with bot in the list)
- **Then**: Bot sends welcome message to the group explaining how users can register
- **And**: Message includes: "👋 Welcome! To use this bot, please run /register to register yourself."
- **And**: Message includes list of available commands or link to /help

**AC46: Bot Added to Group - Multiple Members Added**
- **Given**: Bot is added to group along with other users
- **When**: Bot processes `NEW_CHAT_MEMBERS` update
- **Then**: Bot only reacts when it detects itself in the `new_chat_members` list
- **And**: Bot sends welcome message once (not for each new member)
- **And**: Message is appropriate for the context (explains registration process)

**AC47: Bot Added to Group - Private Chat (No Action)**
- **Given**: Bot is added to a private chat (user starts conversation)
- **When**: User sends first message
- **Then**: `NEW_CHAT_MEMBERS` filter does NOT trigger (only triggers in groups)
- **And**: Bot does NOT send welcome message automatically
- **And**: User can use `/register` or `/start` command directly (normal command flow)

**AC48: Registration - Rate Limiting**
- **Given**: User runs `/register` command
- **When**: User runs `/register` again within 60 seconds
- **Then**: Bot returns success message (idempotent - no rate limit error)
- **And**: No duplicate registrations are created
- **Note**: Rate limiting is handled via idempotency (same user_id = same result), no explicit rate limit needed

**AC49: Registration - Invalid Input (Missing User ID)**
- **Given**: Handler receives update with invalid telegram_user_id (0 or None)
- **When**: RegisterUserUseCase is called
- **Then**: `ValueError` is raised: "Invalid telegram_user_id"
- **And**: User receives friendly error message: "❌ Registration failed: Invalid user information"
- **And**: Error is logged with warning level

## Additional Context

### Dependencies

**Core Dependencies:**
- `python-telegram-bot==20.7` - Telegram Bot API (existing)
- `supabase==2.0.0` - Supabase PostgreSQL client
- `python-dotenv==1.0.0` - Environment variable management
- `pytz==2024.1` - Timezone handling
- `pydantic==2.5.0` - Data validation

**Optional/Development Dependencies:**
- `pytest==7.4.0` - Testing framework
- `pytest-asyncio==0.21.0` - Async testing support
- `pytest-cov==4.1.0` - Code coverage
- `mypy==1.5.0` - Type checking
- `black==23.7.0` - Code formatting
- `ruff==0.0.285` - Linting
- `APScheduler==3.10.0` - Job scheduling
- `structlog==23.1.0` - Structured logging

**Environment Variables:**
- `TELEGRAM_BOT_TOKEN` - Telegram bot token
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase API key
- `ADMIN_USERNAME` - Admin username for admin commands
- `GOOGLE_SHEET_ID` - (Migration only) Google Sheets ID
- `GOOGLE_CREDENTIALS` - (Migration only) Google Sheets credentials JSON

### Testing Strategy

**Unit Tests (70% coverage target):**
- All domain entities and value objects
- All use cases with mocked dependencies (including new: RegisterUserUseCase, AddUserUseCase, SetDefaultTitleUseCase)
- All services (message parsing, title calculation)
- Edge cases: Invalid percentages, locked titles, timezone boundaries, user registration edge cases, default title assignment

**Integration Tests (25% coverage target):**
- All repositories with test Supabase database
- Database transactions
- Statistics calculation with real data
- Message parsing with various formats

**E2E Tests (5% coverage target):**
- Full bot interaction flows
- Mock Telegram API responses (including username resolution for AddUserUseCase)
- Complete use case flows (message → title update → statistics)
- User registration flow (user runs /register → user created → stats check)
- Admin commands flow (admin adds user → admin sets default title → new user registers)
- Bot-added-to-group flow (bot added → welcome message → user registration)

**Test Database:**
- Use separate Supabase project for testing
- Reset database before each test suite
- Use fixtures for common test data

### Database Schema

**Tables:**
1. **users** - Main user data (telegram_user_id, username, title, letter_count, locked, timezone, language)
2. **daily_snapshots** - Daily statistics snapshots (user_id, date, percentage, title, letter_count)
3. **title_history** - All title changes (user_id, old_title, new_title, percentage, change_type)
4. **bot_settings** - Global configuration (key, value, description)
5. **statistics_cache** - Cached statistics (calculation_type, period_days, calculated_value, expires_at)

**Key Design Decisions:**
- `telegram_user_id` as primary identifier (usernames can change)
- `title_letter_count` cached for sorting performance
- `daily_snapshots` for batch statistics calculation
- `statistics_cache` with expiration for performance
- Comprehensive indexes for query performance

### Migration Strategy

**Manual Migration Process:**
1. Export Google Sheets to CSV
2. Run migration script: `python migrations/002_migrate_google_sheets.py --dry-run`
3. Review preview, then execute: `python migrations/002_migrate_google_sheets.py --execute`
4. Validate data migration
5. Rollback if needed: `python migrations/002_migrate_google_sheets.py --rollback`

**Migration Challenges:**
- Google Sheets only has `tg_name` (username), but we need `telegram_user_id`
- Solution: Resolve username → user_id via Telegram Bot API during migration
- If username doesn't exist → Skip with warning, manual intervention required

### Notes

**Key Clarifications from Party Mode Discussion:**
- Message filtering: Only process messages from @HowGayBot (exact username match, case-sensitive)
- Pattern matching: Regex `r"I am (\d+)% gay!"` with 0-100% validation (reject negative or >100)
- Title locking: Prevents auto-updates only, admin can manually change locked titles
- Date boundaries: Process both messages if on different calendar dates (timezone-aware date comparison)
- Letter counting: Spaces excluded, alphanumeric only (regex: `r'[^a-zA-Z0-9]'`)
- Global average: All-time default (period_days=0), customizable period (admin-entered days via command)
- Manual recheck: Admin command to process missed messages from last N days (default: 7 days)
- Statistics: Daily snapshots, batch calculated, cached with expiration (+1 day)

**Architecture Decisions:**
- Clean Architecture with 4 layers (Domain, Application, Infrastructure, Presentation)
- Manual dependency injection (can refactor to DI container later if needed)
- Async/await throughout for consistency with python-telegram-bot 20.7
- Database transactions for title updates to prevent race conditions
- Event-driven statistics calculation (domain events for async processing, future enhancement)
- Connection pooling via supabase-py for optimal database performance
- Telegram API access via infrastructure layer: `TelegramUserResolver` service in infrastructure layer maintains Clean Architecture boundaries (use cases don't depend on bot_instance directly)
- User creation consolidation: `RegisterUserUseCase` handles core user creation logic used by both user registration (`/register`) and admin adding users (`/add_user`), avoiding code duplication

**High-Risk Items & Mitigation:**
- **Migration Risk**: Google Sheets data loss during migration
  - **Mitigation**: Dry-run mode, backup before execution, rollback capability
- **Message Monitoring Risk**: Missing messages if bot is down
  - **Mitigation**: Manual recheck command to process missed messages
- **Race Condition Risk**: Multiple messages processed simultaneously
  - **Mitigation**: Database transactions, unique constraints on daily_snapshots
- **Timezone Risk**: Incorrect date calculations across timezones
  - **Mitigation**: Use pytz for timezone-aware date operations, store user timezone preference

**Known Limitations:**
- Single admin only (from env var, not database-driven)
- Username-based admin check (if user changes username, admin access is lost)
- Manual message monitoring (no automated retry for missed messages)
- Cache expiration is fixed at +1 day (not configurable)
- Russian translations must be manually provided (no automatic translation)
- Username resolution requires chat_id: Telegram Bot API cannot resolve username to user_id without chat context, so `/add_user` command requires chat_id parameter
- Group membership tracking is out of scope: Users are registered globally, not per-group (no groups table or user_group junction table)
- Rate limiting: Registration is idempotent (same user_id = same result), but no explicit rate limiting beyond idempotency

**Future Enhancements (Out of Scope but Noted):**
- Multi-admin support (store admin list in database, not env var)
- Web dashboard interface for statistics and user management
- Real-time push notifications for title changes
- Multiple bot monitoring (currently only @HowGayBot)
- Automatic retry mechanism for failed message processing
- Configurable cache expiration periods
- Admin audit log (track all admin actions separately)
- User language detection (auto-detect from Telegram settings)
- Graph visualization for statistics trends
- Export statistics to CSV/JSON