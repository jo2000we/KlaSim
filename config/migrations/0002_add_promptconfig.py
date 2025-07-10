from django.db import migrations, models
from pathlib import Path

class Migration(migrations.Migration):

    dependencies = [
        ("config", "0001_initial"),
    ]

    def load_defaults(apps, schema_editor):
        PromptConfig = apps.get_model("config", "PromptConfig")
        defaults_path = Path(__file__).resolve().parent.parent / "prompt_defaults.py"
        namespace = {}
        with open(defaults_path) as fh:
            exec(fh.read(), namespace)
        PROMPT_DEFAULTS = namespace["PROMPT_DEFAULTS"]
        for lang, prompts in PROMPT_DEFAULTS.items():
            for ptype, text in prompts.items():
                PromptConfig.objects.create(language=lang, prompt_type=ptype, text=text)

    operations = [
        migrations.CreateModel(
            name="PromptConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("language", models.CharField(choices=[("en", "English"), ("de", "Deutsch")], max_length=5)),
                (
                    "prompt_type",
                    models.CharField(
                        choices=[
                            ("system", "System"),
                            ("base", "Base"),
                            ("level_low", "Level Low"),
                            ("level_medium", "Level Medium"),
                            ("level_high", "Level High"),
                        ],
                        max_length=20,
                    ),
                ),
                ("is_custom", models.BooleanField(default=False)),
                ("text", models.TextField()),
            ],
            options={"unique_together": {("language", "prompt_type")}},
        ),
        migrations.RunPython(load_defaults),
    ]
