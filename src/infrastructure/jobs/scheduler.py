"""Job scheduler setup using APScheduler."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date
import structlog

from .daily_snapshot_job import DailySnapshotJob

logger = structlog.get_logger(__name__)


class JobScheduler:
    """Job scheduler for background tasks."""

    def __init__(
        self,
        daily_snapshot_job: DailySnapshotJob,
    ):
        """Initialize job scheduler."""
        # AsyncIOScheduler will use the current event loop when started
        self._scheduler = AsyncIOScheduler()
        self._daily_snapshot_job = daily_snapshot_job
        self._setup_jobs()

    def _setup_jobs(self) -> None:
        """Setup scheduled jobs."""
        # Daily snapshot job - run at midnight UTC
        self._scheduler.add_job(
            self._run_daily_snapshot,
            CronTrigger(hour=0, minute=0, timezone="UTC"),
            id="daily_snapshot",
            name="Daily Snapshot Creation",
            replace_existing=True,
        )

    async def _run_daily_snapshot(self) -> None:
        """Run daily snapshot job."""
        try:
            snapshot_date = date.today()
            count = await self._daily_snapshot_job.create_daily_snapshots(snapshot_date)
            logger.info("Daily snapshot job completed", count=count)
        except Exception as e:
            logger.error("Daily snapshot job failed", error=str(e), exc_info=True)

    def start(self) -> None:
        """Start the scheduler."""
        self._scheduler.start()
        logger.info("Job scheduler started")

    def shutdown(self) -> None:
        """Shutdown the scheduler."""
        self._scheduler.shutdown()
        logger.info("Job scheduler shut down")
