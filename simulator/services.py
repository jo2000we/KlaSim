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


LEVEL_INSTRUCTIONS = {
    "low": (
        "Bearbeite die Aufgabe so, als wärst du ein schwacher Schüler mit vielen Lücken "
        "und Unsicherheiten. Mache typische Fehler, schreibe knapp oder lückenhaft, "
        "beantworte nur das, was du sicher weißt. Antworte ggf. auch mit Falschantworten, "
        "die im Kontext vorkommen könnten."
    ),
    "medium": (
        "Bearbeite die Aufgabe als durchschnittlicher Schüler: gib solide, aber nicht "
        "perfekte Antworten, manchmal fehlen Details oder es gibt kleinere Fehler."
    ),
    "high": (
        "Bearbeite die Aufgabe als sehr guter Schüler: antworte vollständig, präzise "
        "und mit korrekter Fachsprache. Gehe auch auf Details und Hintergründe ein, "
        "sofern sie im Kontext stehen."
    ),
}

BASE_INSTRUCTION = (
    "Nutze ausschließlich die folgenden Kontextinformationen als Wissensquelle. "
    "Beantworte die Klausuraufgabe so, wie es ein Schüler auf dem angegebenen Leistungsniveau tun würde. "
    "Gib ausschließlich den Lösungstext, ohne Einleitung, Erklärung oder Wiederholung der Aufgabe. "
    "Wenn dir Informationen fehlen, antworte wie ein Schüler, der das Thema nicht vollständig versteht. "
    "Der Antwortstil soll dem einer echten Schülerklausur entsprechen: schreibe klar, aber nicht überperfekt. "
    "Keine Kommentare, keine Meta-Texte. Die Antworten sollen sich sprachlich, inhaltlich und vom Stil an echten Schülerantworten orientieren. "
    "Niemals den Aufgabenstellungstext wiederholen oder Zusammenfassungen geben."
)


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

    results: List[AIResult] = []
    for level, instruction in LEVEL_INSTRUCTIONS.items():
        messages = [
            {
                "role": "system",
                "content": (
                    "Du bist ein Sch\u00fcler, der eine Klausur schreibt. "
                    "Alle Antworten sollen realistisch wirken und keine Einleitungen oder Kommentare enthalten. "
                    "Die Antworten sollen sich sprachlich, inhaltlich und vom Stil an echten Sch\u00fclerantworten orientieren. "
                    "Niemals den Aufgabenstellungstext wiederholen oder Zusammenfassungen geben."
                ),
            },
            {
                "role": "user",
                "content": f"{base_prompt}\n\n{BASE_INSTRUCTION}\n{instruction}",
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
