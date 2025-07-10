from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.core.management import call_command
from django.http import HttpResponse
import io
import zipfile
import openai
from django.utils import translation

from .models import AppConfig, PromptConfig
from .forms import SetupForm, LoginForm, SettingsForm, PromptForm
from .prompt_defaults import PROMPT_DEFAULTS



def admin_login_required(view_func):
    def wrapped(request, *args, **kwargs):
        if not request.session.get("admin_logged_in"):
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return wrapped


def _check_openai_key(key: str) -> bool:
    """Return True if the given key can access the OpenAI API."""
    try:
        client = openai.OpenAI(api_key=key)
        client.models.list()
        return True
    except Exception:
        return False


def setup_view(request):
    config = AppConfig.get_solo()
    if config.setup_complete:
        return redirect('index')

    if request.method == 'POST':
        form = SetupForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = SetupForm(instance=config)
    return render(request, 'config/setup.html', {'form': form})


@admin_login_required
def test_api_key_view(request):
    """Return JSON indicating whether the provided or stored key is valid."""
    config = AppConfig.get_solo()
    key = request.POST.get("api_key") or config.openai_api_key
    return JsonResponse({"ok": _check_openai_key(key)})


def login_view(request):
    config = AppConfig.get_solo()
    if not config.setup_complete:
        return redirect("setup")

    error = None
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            if config.check_admin_password(form.cleaned_data["password"]):
                request.session["admin_logged_in"] = True
                return redirect("settings")
            error = "Invalid password"
    else:
        form = LoginForm()
    return render(request, "config/login.html", {"form": form, "error": error})


@admin_login_required
def settings_view(request):
    config = AppConfig.get_solo()
    display_lang = request.GET.get("lang", config.language)
    translation.activate(display_lang)
    request.session['django_language'] = display_lang
    prompts = {}
    for ptype in ["system", "base", "level_low", "level_medium", "level_high"]:
        pc = PromptConfig.objects.filter(language=display_lang, prompt_type=ptype).first()
        if pc:
            prompts[f"{ptype}_custom"] = pc.is_custom
            prompts[f"{ptype}_text"] = pc.text if pc.is_custom else PROMPT_DEFAULTS[display_lang][ptype]
        else:
            prompts[f"{ptype}_custom"] = False
            prompts[f"{ptype}_text"] = PROMPT_DEFAULTS[display_lang][ptype]

    if request.method == "POST":
        form = SettingsForm(request.POST, instance=config)
        prompt_form = PromptForm(request.POST)
        if form.is_valid() and prompt_form.is_valid():
            form.save()
            display_lang = form.cleaned_data["language"]
            translation.activate(display_lang)
            request.session['django_language'] = display_lang
            for ptype in ["system", "base", "level_low", "level_medium", "level_high"]:
                pc, _ = PromptConfig.objects.get_or_create(language=display_lang, prompt_type=ptype)
                use_custom = prompt_form.cleaned_data[f"{ptype}_custom"]
                if use_custom:
                    pc.text = prompt_form.cleaned_data[f"{ptype}_text"]
                    pc.is_custom = True
                else:
                    pc.text = PROMPT_DEFAULTS[display_lang][ptype]
                    pc.is_custom = False
                pc.save()
            messages.success(request, "Settings saved")
            return redirect(f"{reverse('settings')}?lang={display_lang}")
    else:
        form = SettingsForm(instance=config, initial={"language": display_lang})
        prompt_form = PromptForm(initial=prompts)

    key_valid = _check_openai_key(config.openai_api_key)
    context = {
        "form": form,
        "prompt_form": prompt_form,
        "key_valid": key_valid,
        "language": display_lang,
        "sim_pw_set": bool(config.simulation_password_hash),
    }
    return render(request, "config/settings.html", context)


def logout_view(request):
    request.session.pop("admin_logged_in", None)
    return redirect("index")


@admin_login_required
def sessions_view(request):
    """Display all sessions with download options."""
    from simulator.models import ContextFile, ExamFile, AIResult

    session_ids = set(
        ContextFile.objects.values_list("session_id", flat=True)
    ) | set(ExamFile.objects.values_list("session_id", flat=True)) | set(
        AIResult.objects.values_list("session_id", flat=True)
    )
    sessions = []
    for sid in session_ids:
        sessions.append(
            {
                "id": sid,
                "context": list(ContextFile.objects.filter(session_id=sid)),
                "exam": list(ExamFile.objects.filter(session_id=sid)),
                "results": list(AIResult.objects.filter(session_id=sid)),
            }
        )
    return render(request, "config/sessions.html", {"sessions": sessions})


@admin_login_required
def download_session_zip(request, session_id: str):
    """Return a zip file containing all data for a session."""
    from simulator.models import ContextFile, ExamFile, AIResult

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for obj in ExamFile.objects.filter(session_id=session_id):
            zf.write(obj.file.path, obj.file.name.split("/", 1)[-1])
        for obj in ContextFile.objects.filter(session_id=session_id):
            zf.write(obj.file.path, obj.file.name.split("/", 1)[-1])
        for obj in AIResult.objects.filter(session_id=session_id):
            zf.write(obj.file.path, obj.file.name.split("/", 1)[-1])
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response[
        "Content-Disposition"
    ] = f"attachment; filename=session_{session_id}.zip"
    return response


@admin_login_required
def cleanup_sessions_view(request):
    """Delete all stored sessions and files."""
    if request.method == "POST":
        call_command("clean_sessions", all=True)
        messages.success(request, "Sessions deleted")
    return redirect("sessions")
