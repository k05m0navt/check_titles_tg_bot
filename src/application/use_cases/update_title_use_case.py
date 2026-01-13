"""Update title use case - core business logic for title management."""

from typing import Optional
from datetime import date, datetime
import structlog
import pytz

from ...domain.entities.user import User
from ...domain.value_objects.percentage import Percentage
from ...domain.value_objects.title import Title
from ...domain.value_objects.timezone import Timezone
from ...domain.repositories.user_repository import IUserRepository
from ...domain.repositories.statistics_repository import IStatisticsRepository
from ...domain.repositories.title_history_repository import ITitleHistoryRepository
from ...domain.services.title_calculation_service import TitleCalculationService, IActiveUserCounter
from ...domain.exceptions import TitleLockedError, UserNotFoundError

logger = structlog.get_logger(__name__)


class UpdateTitleUseCase:
    """Use case for updating user title based on percentage from @HowGayBot."""

    def __init__(
        self,
        user_repository: IUserRepository,
        statistics_repository: IStatisticsRepository,
        title_history_repository: ITitleHistoryRepository,
        title_calculation_service: TitleCalculationService,
    ):
        """
        Initialize update title use case.
        
        Args:
            user_repository: User repository interface
            statistics_repository: Statistics repository interface
            title_history_repository: Title history repository interface
            title_calculation_service: Title calculation service
        """
        self._user_repository = user_repository
        self._statistics_repository = statistics_repository
        self._title_history_repository = title_history_repository
        self._title_calculation_service = title_calculation_service

    async def execute(
        self, telegram_user_id: int, percentage: Percentage, message_date: date
    ) -> None:
        """
        Execute title update use case.
        
        Args:
            telegram_user_id: Telegram user ID (from message.from_user.id)
            percentage: Percentage value object (0-100)
            message_date: Date of the message (timezone-aware)
            
        Raises:
            UserNotFoundError: If user not found
            TitleLockedError: If title is locked and not first message today
        """
        # Get user by Telegram user ID
        user = await self._user_repository.get_by_telegram_id(telegram_user_id)
        if not user:
            raise UserNotFoundError(f"User with Telegram ID {telegram_user_id} not found")

        # Check if title is locked
        if user.title_locked:
            raise TitleLockedError("Title is locked and cannot be updated automatically")

        # Note: The title_calculation_service will handle empty full_title gracefully
        # by returning an empty Title. No need to check here - if full_title is not set,
        # the displayed title will just be empty, which is acceptable behavior.

        # Check if this is first message today (timezone-aware)
        # Convert date to datetime at midnight, localize to user's timezone, then convert back to date
        user_timezone = pytz.timezone(str(user.timezone))
        message_datetime = datetime.combine(message_date, datetime.min.time())
        message_date_aware = user_timezone.localize(message_datetime).date()

        if not user.is_first_message_today(message_date_aware):
            # Not first message today, skip
            return

        # Calculate displayed title by incrementing/decrementing from current title based on percentage
        logger.debug(
            "Starting title calculation",
            telegram_user_id=telegram_user_id,
            percentage=int(percentage),
            current_title=str(user.title),
            current_title_letter_count=user.title.letter_count(),
            full_title=str(user.full_title),
            full_title_letter_count=user.full_title.letter_count()
        )
        
        displayed_title = await self._title_calculation_service.calculate_displayed_title(
            user.full_title, percentage, user.title
        )

        # Save old displayed title for history (not full_title)
        old_title_str = str(user.title)

        logger.debug(
            "Title calculation completed",
            telegram_user_id=telegram_user_id,
            percentage=int(percentage),
            old_title=old_title_str,
            old_title_letter_count=user.title.letter_count(),
            new_title=str(displayed_title),
            new_title_letter_count=displayed_title.letter_count()
        )

        # Update displayed title (full_title remains unchanged)
        # The calculation service returns a valid substring of full_title (can be empty)
        user.update_title(displayed_title)
        
        user.last_percentage = percentage
        user.update_last_processed_date(message_date_aware)

        # Save user (upsert returns user with ID set)
        saved_user = await self._user_repository.save(user)
        if not saved_user.id:
            raise ValueError("User ID not set after save")

        # Create title history entry (track displayed title changes)
        await self._title_history_repository.save(
            user_id=saved_user.id,
            old_title=old_title_str if old_title_str else None,
            new_title=str(displayed_title),
            percentage=int(percentage),
            change_type="automatic",
        )

        # Create daily snapshot (idempotent, will be created only once per day)
        # Store displayed title (not full_title) in snapshot
        await self._statistics_repository.create_daily_snapshot(
            user_id=saved_user.id,
            snapshot_date=message_date_aware,
            percentage=int(percentage),
            title=str(displayed_title),
            title_letter_count=displayed_title.letter_count(),
        )


# Adapter to make UserRepository work as IActiveUserCounter for TitleCalculationService
class UserRepositoryActiveCounter(IActiveUserCounter):
    """Adapter to use UserRepository as IActiveUserCounter."""

    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository

    async def count_active_users(self) -> int:
        """Count active users (all users in database)."""
        return await self._user_repository.count_active_users()
