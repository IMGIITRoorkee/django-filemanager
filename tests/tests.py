from django.core.urlresolvers import reverse
from django.test import Client, TestCase


class FilemanagerTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_view_returns_200(self):
        url = reverse('view', kwargs={'path': ''})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
