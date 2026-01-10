# Architecture Documentation

## Overview

This Telegram bot follows Clean Architecture principles with clear separation of concerns across four layers: Domain, Application, Infrastructure, and Presentation.

## Architecture Layers

### Domain Layer (`src/domain/`)

**Responsibility**: Core business logic and entities

**Components**:
- **Entities**: `User` - Core user entity with title management
- **Value Objects**: `Title`, `Percentage`, `Timezone` - Immutable domain concepts
- **Services**: `TitleCalculationService` - Domain-specific business logic
- **Repositories** (Interfaces): Abstract interfaces for data access
- **Exceptions**: Domain-specific error types

**Dependencies**: None (pure domain logic)

### Application Layer (`src/application/`)

**Responsibility**: Use cases and application services

**Components**:
- **Use Cases**: 
  - `UpdateTitleUseCase` - Core title update logic
  - `GetUserStatsUseCase` - User statistics retrieval
  - `GetLeaderboardUseCase` - Leaderboard generation
  - `CalculateStatisticsUseCase` - Global statistics calculation
  - Admin use cases (lock/unlock title, set period)
- **Services**: 
  - `MessageParser` - Parse @HowGayBot messages
  - `AdminService` - Admin validation logic

**Dependencies**: Domain layer only

### Infrastructure Layer (`src/infrastructure/`)

**Responsibility**: External concerns and technical implementation

**Components**:
- **Database**: Supabase client and repository implementations
- **Config**: Environment variable management
- **Jobs**: Background job scheduling (daily snapshots, statistics)
- **Logging**: Structured logging configuration
- **i18n**: Localization/translation system

**Dependencies**: Domain and Application layers

### Presentation Layer (`src/presentation/`)

**Responsibility**: Telegram bot interface

**Components**:
- **Handlers**: Command handlers, message handlers, callback handlers, inline query handlers
- **Keyboards**: Inline keyboard builder
- **Utils**: Localization utilities
- **Errors**: Global error handler
- **Main**: Application entry point and dependency injection setup

**Dependencies**: All other layers

## Dependency Flow

```
Presentation → Application → Domain ← Infrastructure
```

- Presentation depends on Application and Infrastructure
- Application depends on Domain only
- Infrastructure implements Domain interfaces
- Domain has no dependencies (pure business logic)

## Design Patterns

### Repository Pattern

Abstract interfaces in Domain layer, concrete implementations in Infrastructure layer. Enables easy testing and swapping implementations.

### Use Case Pattern

Each feature is encapsulated in a use case class with an `execute()` method. Clear input/output contracts.

### Dependency Injection

Manual dependency injection via constructor parameters. Dependencies are wired in `main.py`.

### Value Objects

Immutable domain concepts (Title, Percentage, Timezone) with validation and business logic.

## Database Schema

See `docs/database_schema.md` for complete schema documentation.

**Key Tables**:
- `users` - Main user data
- `daily_snapshots` - Daily statistics snapshots
- `title_history` - Complete title change history
- `bot_settings` - Global configuration
- `statistics_cache` - Cached calculations

## Message Flow

1. **Message Monitoring**: Bot listens for messages from @HowGayBot
2. **Message Parsing**: Extract percentage using regex pattern
3. **User Identification**: Identify target user from reply context
4. **Title Update**: Use case executes title calculation and update
5. **Statistics**: Create daily snapshot and update statistics cache

## Title Calculation Rules

- **0%**: Add 3 letters
- **1-5%**: Add 1 letter
- **95-99%**: Remove 1 letter
- **100%**: Remove N letters (where N = active user count, always queried fresh)

## Error Handling

- Domain exceptions at domain layer
- Global error handler at presentation layer
- Structured logging throughout
- User-friendly error messages via localization

## Background Jobs

- **Daily Snapshot Job**: Runs at midnight UTC, creates snapshots for active users
- **Statistics Calculation**: Calculates and caches global statistics
- **Cache Cleanup**: Removes expired cache entries

## Testing Strategy

- **Unit Tests**: Domain models, services, use cases with mocked dependencies
- **Integration Tests**: Repository implementations with test database
- **E2E Tests**: Full bot interaction flows with mocked Telegram API

## Deployment

See `README.md` for deployment instructions. The bot uses Railway with a Procfile for deployment.
