from django import forms
from .models import AppConfig
from django.utils.translation import gettext_lazy as _


class SetupForm(forms.ModelForm):
    admin_password = forms.CharField(label=_("Admin password"), widget=forms.PasswordInput)
    simulation_password = forms.CharField(label=_("Simulation password"), widget=forms.PasswordInput, required=False)

    class Meta:
        model = AppConfig
        fields = ["openai_api_key", "language"]
        labels = {
            "openai_api_key": _("OpenAI API Key"),
            "language": _("Language"),
        }

    def save(self, commit=True):
        config = super().save(commit=False)
        password = self.cleaned_data.get("admin_password")
        if password:
            config.set_admin_password(password)
        sim_pw = self.cleaned_data.get("simulation_password")
        config.set_simulation_password(sim_pw)
        config.setup_complete = True
        if commit:
            config.save()
        return config


class LoginForm(forms.Form):
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput)


class SettingsForm(forms.ModelForm):
    new_password = forms.CharField(
        label=_("New settings password"),
        widget=forms.PasswordInput(attrs={"style": "display:none;"}),
        required=False,
    )
    simulation_password = forms.CharField(
        label=_("Simulation password"),
        widget=forms.PasswordInput,
        required=False,
    )

    class Meta:
        model = AppConfig
        fields = ["openai_api_key", "language"]
        labels = {
            "openai_api_key": _("OpenAI API Key"),
            "language": _("Language"),
        }

    def save(self, commit=True):
        config = super().save(commit=False)
        new_password = self.cleaned_data.get("new_password")
        if new_password:
            config.set_admin_password(new_password)
        config.set_simulation_password(self.cleaned_data.get("simulation_password"))
        if commit:
            config.save()
        return config


class PromptForm(forms.Form):
    system_custom = forms.BooleanField(required=False)
    system_text = forms.CharField(widget=forms.Textarea, required=False)
    base_custom = forms.BooleanField(required=False)
    base_text = forms.CharField(widget=forms.Textarea, required=False)
    level_low_custom = forms.BooleanField(required=False)
    level_low_text = forms.CharField(widget=forms.Textarea, required=False)
    level_medium_custom = forms.BooleanField(required=False)
    level_medium_text = forms.CharField(widget=forms.Textarea, required=False)
    level_high_custom = forms.BooleanField(required=False)
    level_high_text = forms.CharField(widget=forms.Textarea, required=False)
