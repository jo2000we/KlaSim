from django import forms
import os


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
        return uploaded
