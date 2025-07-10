from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from config.models import AppConfig

class SessionViewsTest(TestCase):
    def setUp(self):
        config = AppConfig.get_solo()
        config.set_admin_password('pw')
        config.openai_api_key = 'key'
        config.setup_complete = True
        config.save()
        self.client.post(reverse('login'), {'password': 'pw'})

    def test_sessions_view_access(self):
        response = self.client.get(reverse('sessions'))
        self.assertEqual(response.status_code, 200)

    def test_cleanup_redirect(self):
        response = self.client.post(reverse('cleanup_sessions'))
        self.assertEqual(response.status_code, 302)
