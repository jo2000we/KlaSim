"""Database models for the simulator app."""

from django.db import models


class ContextFile(models.Model):
    """File uploaded as additional context during a session."""

    file = models.FileField(upload_to="context_files/")
    upload_time = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=40)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"ContextFile({self.file.name}) for {self.session_id}"


class ExamFile(models.Model):
    """The exam file uploaded for a session."""

    file = models.FileField(upload_to="exam_files/")
    upload_time = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=40)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"ExamFile({self.file.name}) for {self.session_id}"


class AIResult(models.Model):
    """Result data produced by the AI."""

    file = models.FileField(upload_to="ai_results/")

    LEVEL_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    session_id = models.CharField(max_length=40)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"AIResult({self.level}) for {self.session_id}"

