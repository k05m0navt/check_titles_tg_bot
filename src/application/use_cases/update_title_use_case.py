"""Update title use case - core business logic for title management."""

from typing import Optional
from datetime import date
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
        user_timezone = pytz.timezone(str(user.timezone))
        message_date_aware = user_timezone.localize(
            message_date.replace(hour=0, minute=0, second=0)
        ).date() if isinstance(message_date, date) else message_date

        if not user.is_first_message_today(message_date_aware):
            # Not first message today, skip
            return

        # Calculate displayed title from full_title based on percentage
        displayed_title = await self._title_calculation_service.calculate_displayed_title(
            user.full_title, percentage
        )

        # Edge case: if calculated letter count < 0, set to empty string
        if displayed_title.letter_count() < 0:
            displayed_title = Title("")

        # Save old displayed title for history (not full_title)
        old_title_str = str(user.title)

        # Update displayed title (full_title remains unchanged)
        user.update_title(displayed_title)
        user.last_percentage = percentage
        user.update_last_processed_date(message_date_aware)

        # Save user (transaction)
        await self._user_repository.save(user)

        # Save user again to ensure ID is set
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
