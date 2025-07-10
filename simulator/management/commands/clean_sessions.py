from datetime import timedelta
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.db import OperationalError
from django.utils import timezone

from simulator.models import ContextFile, ExamFile, AIResult


class Command(BaseCommand):
    """Delete files and DB entries for sessions."""

    help = (
        "Remove uploaded files and database objects for stale sessions "
        "and clear expired Django sessions. Use --all to remove everything."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Delete all sessions regardless of age",
        )

    def handle(self, *args, **options):
        lifetime = getattr(settings, "SESSION_LIFETIME_DAYS", 7)
        cutoff = timezone.now() - timedelta(days=lifetime)

        try:
            if options.get("all"):
                session_ids = set(ContextFile.objects.values_list("session_id", flat=True))
                session_ids.update(ExamFile.objects.values_list("session_id", flat=True))
                session_ids.update(AIResult.objects.values_list("session_id", flat=True))
            else:
                session_ids = set(
                    ContextFile.objects.filter(upload_time__lt=cutoff).values_list("session_id", flat=True)
                )
                session_ids.update(
                    ExamFile.objects.filter(upload_time__lt=cutoff).values_list("session_id", flat=True)
                )
                session_ids.update(
                    AIResult.objects.filter(session_id__in=session_ids).values_list("session_id", flat=True)
                )
        except OperationalError:
            self.stdout.write("Database not initialized; skipping cleanup.")
            return

        if session_ids:
            for sid in session_ids:
                for model in [ContextFile, ExamFile, AIResult]:
                    for obj in model.objects.filter(session_id=sid):
                        if hasattr(obj, "file"):
                            obj.file.delete(save=False)
                        obj.delete()

                session_dir = Path(settings.MEDIA_ROOT) / "ai_results" / sid
                if session_dir.exists():
                    shutil.rmtree(session_dir, ignore_errors=True)

            label = "session(s)" if options.get("all") else "stale session(s)"
            self.stdout.write(f"Deleted {len(session_ids)} {label}.")
        else:
            self.stdout.write("No stale sessions found.")

        # Also clear expired Django sessions
        call_command("clearsessions")
