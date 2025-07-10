from datetime import timedelta
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.db import OperationalError
from django.utils import timezone

from simulator.models import ContextFile, ExamFile, AIResult


class Command(BaseCommand):
    """Delete session files and DB entries."""

    help = (
        "Remove uploaded files and database objects for stale sessions "
        "and clear expired Django sessions."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Delete all sessions regardless of age",
        )

    def handle(self, *args, **options):
        if options.get("all"):
            cutoff = None
        else:
            lifetime = getattr(settings, "SESSION_LIFETIME_DAYS", 7)
            cutoff = timezone.now() - timedelta(days=lifetime)

        try:
            if cutoff is None:
                ctx_qs = ContextFile.objects.all()
                exam_qs = ExamFile.objects.all()
            else:
                ctx_qs = ContextFile.objects.filter(upload_time__lt=cutoff)
                exam_qs = ExamFile.objects.filter(upload_time__lt=cutoff)

            session_ids = set(ctx_qs.values_list("session_id", flat=True))
            session_ids.update(exam_qs.values_list("session_id", flat=True))
            session_ids.update(AIResult.objects.values_list("session_id", flat=True))
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

            self.stdout.write(f"Deleted {len(session_ids)} stale session(s).")
        else:
            self.stdout.write("No stale sessions found.")

        # Also clear expired Django sessions
        call_command("clearsessions")
