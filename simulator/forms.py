from django import forms
import os
import re


class ContextUploadForm(forms.Form):
    """Form for uploading additional context files."""

    file = forms.FileField()

    ALLOWED_EXTENSIONS = {".txt", ".csv", ".pdf", ".docx"}

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        ext = os.path.splitext(uploaded.name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                "Unsupported file type. Allowed: "
                + ", ".join(sorted(self.ALLOWED_EXTENSIONS))
            )
        return uploaded


class ExamUploadForm(forms.Form):
    """Form for uploading an exam file."""

    file = forms.FileField()

    ALLOWED_EXTENSIONS = {".docx"}

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        ext = os.path.splitext(uploaded.name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                "Unsupported file type. Allowed: "
                + ", ".join(sorted(self.ALLOWED_EXTENSIONS))
            )
        if ext == ".docx":
            try:
                from docx import Document

                doc = Document(uploaded)
                text = "\n".join(p.text for p in doc.paragraphs).lower()
                if re.search(r"(low|medium|high)\s+(antwort|answer)", text):
                    raise forms.ValidationError(
                        "Uploaded file appears to be an AI result. Please use the original exam file."
                    )
            except Exception:
                # If parsing fails we ignore the check but reset file pointer
                pass
            finally:
                uploaded.seek(0)
        return uploaded
