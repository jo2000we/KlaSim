from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class AppConfig(models.Model):
    """Singleton-style configuration for the application."""

    admin_password_hash = models.CharField(max_length=128)
    openai_api_key = models.CharField(max_length=100)
    simulation_password_hash = models.CharField(max_length=128, blank=True)
    language = models.CharField(max_length=5, choices=[("en", "English"), ("de", "Deutsch")], default="en")
    setup_complete = models.BooleanField(default=False)

    @classmethod
    def get_solo(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config

    def set_admin_password(self, raw_password: str) -> None:
        self.admin_password_hash = make_password(raw_password)

    def check_admin_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.admin_password_hash)

    def set_simulation_password(self, raw_password: str | None) -> None:
        self.simulation_password_hash = (
            make_password(raw_password) if raw_password else ""
        )

    def check_simulation_password(self, raw_password: str) -> bool:
        if not self.simulation_password_hash:
            return True
        return check_password(raw_password, self.simulation_password_hash)


class PromptConfig(models.Model):
    LANGUAGE_CHOICES = [("en", "English"), ("de", "Deutsch")]
    PROMPT_TYPES = [
        ("system", "System"),
        ("base", "Base"),
        ("level_low", "Level Low"),
        ("level_medium", "Level Medium"),
        ("level_high", "Level High"),
    ]

    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES)
    prompt_type = models.CharField(max_length=20, choices=PROMPT_TYPES)
    is_custom = models.BooleanField(default=False)
    text = models.TextField()

    class Meta:
        unique_together = ("language", "prompt_type")

