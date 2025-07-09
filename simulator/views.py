from __future__ import annotations

import uuid

from django.shortcuts import get_object_or_404, redirect, render

from .forms import ContextUploadForm, ExamUploadForm
from .models import ContextFile, ExamFile


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
    context_files = (
        ContextFile.objects.filter(session_id=session_id) if session_id else []
    )
    exam_files = ExamFile.objects.filter(session_id=session_id) if session_id else []
    return render(
        request,
        "simulator/index.html",
        {
            "context_form": ContextUploadForm(),
            "exam_form": ExamUploadForm(),
            "context_files": context_files,
            "exam_files": exam_files,
            "session_id": session_id,
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
        return render(
            request,
            "simulator/index.html",
            {
                "context_form": form,
                "exam_form": ExamUploadForm(),
                "context_files": context_files,
                "exam_files": exam_files,
                "session_id": session_id,
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
        return render(
            request,
            "simulator/index.html",
            {
                "context_form": ContextUploadForm(),
                "exam_form": form,
                "context_files": context_files,
                "exam_files": exam_files,
                "session_id": session_id,
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
