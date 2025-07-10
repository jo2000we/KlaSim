from __future__ import annotations

import uuid

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from django.contrib import messages
from django.conf import settings

from .forms import ContextUploadForm, ExamUploadForm
from .models import ContextFile, ExamFile, AIResult
from config.models import AppConfig
from config.views import _check_openai_key
from .services import generate_ai_results


def _ensure_session_id(request) -> str:
    """Return a session ID, creating one if needed."""
    session_id = request.session.get("session_id")
    if not session_id:
        session_id = uuid.uuid4().hex
        request.session["session_id"] = session_id
    return session_id


def index(request):
    """Display upload forms and current session files."""
    session_id = request.session.get("session_id")
    config = AppConfig.get_solo()
    context_files = (
        ContextFile.objects.filter(session_id=session_id) if session_id else []
    )
    exam_files = ExamFile.objects.filter(session_id=session_id) if session_id else []
    ai_results = AIResult.objects.filter(session_id=session_id) if session_id else []
    key_ok = _check_openai_key(config.openai_api_key)
    if not config.setup_complete:
        status = {
            "text": "Setup required",
            "class": "warning",
            "url": reverse("setup"),
        }
    elif not key_ok:
        status = {
            "text": "Key Fail",
            "class": "error",
            "url": reverse("settings"),
        }
    else:
        status = {
            "text": "Active",
            "class": "ok",
            "url": reverse("settings"),
        }

    return render(
        request,
        "simulator/index.html",
        {
            "context_form": ContextUploadForm(),
            "exam_form": ExamUploadForm(),
            "context_files": context_files,
            "exam_files": exam_files,
            "session_id": session_id,
            "ai_results": ai_results,
            "status": status,
            "sim_password_required": bool(config.simulation_password_hash),
        },
    )


def upload_context(request):
    """Handle context file uploads."""
    if request.method == "POST":
        form = ContextUploadForm(request.POST, request.FILES)
        if form.is_valid():
            session_id = _ensure_session_id(request)
            ContextFile.objects.create(
                file=form.cleaned_data["file"], session_id=session_id
            )
            return redirect("index")
        session_id = request.session.get("session_id")
        context_files = (
            ContextFile.objects.filter(session_id=session_id) if session_id else []
        )
        exam_files = ExamFile.objects.filter(session_id=session_id) if session_id else []
        config = AppConfig.get_solo()
        key_ok = _check_openai_key(config.openai_api_key)
        if not config.setup_complete:
            status = {"text": "Setup required", "class": "warning", "url": reverse("setup")}
        elif not key_ok:
            status = {"text": "Key Fail", "class": "error", "url": reverse("settings")}
        else:
            status = {"text": "Active", "class": "ok", "url": reverse("settings")}
        return render(
            request,
            "simulator/index.html",
            {
                "context_form": form,
                "exam_form": ExamUploadForm(),
                "context_files": context_files,
                "exam_files": exam_files,
                "session_id": session_id,
                "ai_results": AIResult.objects.filter(session_id=session_id) if session_id else [],
                "status": status,
                "sim_password_required": bool(config.simulation_password_hash),
            },
        )
    return redirect("index")


def upload_exam(request):
    """Handle exam file uploads."""
    if request.method == "POST":
        form = ExamUploadForm(request.POST, request.FILES)
        if form.is_valid():
            session_id = _ensure_session_id(request)
            ExamFile.objects.filter(session_id=session_id).delete()
            ExamFile.objects.create(
                file=form.cleaned_data["file"], session_id=session_id
            )
            return redirect("index")
        session_id = request.session.get("session_id")
        context_files = (
            ContextFile.objects.filter(session_id=session_id) if session_id else []
        )
        exam_files = ExamFile.objects.filter(session_id=session_id) if session_id else []
        config = AppConfig.get_solo()
        key_ok = _check_openai_key(config.openai_api_key)
        if not config.setup_complete:
            status = {"text": "Setup required", "class": "warning", "url": reverse("setup")}
        elif not key_ok:
            status = {"text": "Key Fail", "class": "error", "url": reverse("settings")}
        else:
            status = {"text": "Active", "class": "ok", "url": reverse("settings")}
        return render(
            request,
            "simulator/index.html",
            {
                "context_form": ContextUploadForm(),
                "exam_form": form,
                "context_files": context_files,
                "exam_files": exam_files,
                "session_id": session_id,
                "ai_results": AIResult.objects.filter(session_id=session_id) if session_id else [],
                "status": status,
                "sim_password_required": bool(config.simulation_password_hash),
            },
        )
    return redirect("index")


def delete_context(request, pk: int):
    """Remove a context file from the current session."""
    session_id = request.session.get("session_id")
    file_obj = get_object_or_404(ContextFile, pk=pk, session_id=session_id)
    file_obj.file.delete(save=False)
    file_obj.delete()
    return redirect("index")


def delete_exam(request, pk: int):
    """Remove an exam file from the current session."""
    session_id = request.session.get("session_id")
    file_obj = get_object_or_404(ExamFile, pk=pk, session_id=session_id)
    file_obj.file.delete(save=False)
    file_obj.delete()
    return redirect("index")


def run_simulation(request):
    """Execute the AI simulation for the current session."""
    session_id = request.session.get("session_id")
    config = AppConfig.get_solo()
    if not config.setup_complete:
        return redirect("setup")
    if not session_id:
        return redirect("index")

    if not _check_openai_key(config.openai_api_key):
        messages.error(request, "Ungültiger OpenAI API Key")
        return redirect("index")

    if config.simulation_password_hash:
        sim_pw = request.POST.get("sim_password", "")
        if not config.check_simulation_password(sim_pw):
            messages.error(request, "Falsches Passwort")
            return redirect("index")

    try:
        generate_ai_results(session_id, api_key=config.openai_api_key)
        messages.success(request, "Simulation abgeschlossen.")
    except Exception as exc:  # pragma: no cover - best effort
        messages.error(request, f"Simulation fehlgeschlagen: {exc}")

    return redirect("index")
