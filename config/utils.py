from .models import AppConfig, PromptConfig
from .prompt_defaults import PROMPT_DEFAULTS


def load_prompts() -> dict:
    config = AppConfig.get_solo()
    prompts = {}
    language = config.language
    for ptype in ["system", "base", "level_low", "level_medium", "level_high"]:
        pc = PromptConfig.objects.filter(language=language, prompt_type=ptype).first()
        if pc and pc.is_custom:
            prompts[ptype] = pc.text
        else:
            prompts[ptype] = PROMPT_DEFAULTS[language][ptype]
    return prompts
