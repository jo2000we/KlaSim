from __future__ import annotations

import os
import csv
from pathlib import Path
from typing import List

MAX_PROMPT_CHARS = 25000

from django.conf import settings
from django.core.files.base import File

import openai
from docx import Document
from PyPDF2 import PdfReader

from .models import AIResult, ContextFile, ExamFile
from config.utils import load_prompts




def _read_file(path: str) -> str:
    """Return text content from a file path."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    if ext == ".csv":
        with open(path, newline="", encoding="utf-8", errors="ignore") as fh:
            reader = csv.reader(fh)
            return "\n".join(",".join(row) for row in reader)
    if ext == ".pdf":
        try:
            with open(path, "rb") as fh:
                reader = PdfReader(fh)
                return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception:
            return ""
    # Fallback to plain text
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read()


def assemble_prompt(session_id: str) -> str:
    """Create a base prompt from uploaded exam and context files."""
    exam = ExamFile.objects.filter(session_id=session_id).first()
    if not exam:
        raise ValueError("No exam file uploaded")
    context_files = ContextFile.objects.filter(session_id=session_id)

    exam_text = _read_file(exam.file.path)
    context_text = "\n\n".join(_read_file(c.file.path) for c in context_files)

    prompt = f"Exam:\n{exam_text}\n\nAdditional context:\n{context_text}"
    if len(prompt) > MAX_PROMPT_CHARS:
        raise ValueError("Zu viele oder zu große Kontextdateien f\u00fcr die KI")
    return prompt


def generate_ai_results(session_id: str, *, api_key: str | None = None) -> List[AIResult]:
    """Generate AI answers for all performance levels."""
    base_prompt = assemble_prompt(session_id)
    client = openai.OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    storage_root = getattr(settings, "MEDIA_ROOT", "")
    session_dir = Path(storage_root) / "ai_results" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Remove old results for this session
    for old in AIResult.objects.filter(session_id=session_id):
        old.file.delete(save=False)
        old.delete()

    prompts = load_prompts()
    results: List[AIResult] = []
    level_map = {
        "low": prompts["level_low"],
        "medium": prompts["level_medium"],
        "high": prompts["level_high"],
    }
    for level, instruction in level_map.items():
        messages = [
            {"role": "system", "content": prompts["system"]},
            {
                "role": "user",
                "content": f"{base_prompt}\n\n{prompts['base']}\n{instruction}",
            },
        ]
        model = getattr(settings, "OPENAI_MODEL", "gpt-4-1106-preview")
        response = client.chat.completions.create(model=model, messages=messages)
        answer = response.choices[0].message.content.strip()

        doc = Document()
        doc.add_paragraph(answer)
        file_name = f"{level}.docx"
        file_path = session_dir / file_name
        doc.save(file_path)

        result = AIResult(level=level, session_id=session_id)
        with open(file_path, "rb") as fh:
            result.file.save(f"{session_id}/{file_name}", File(fh), save=True)
        results.append(result)

    return results
