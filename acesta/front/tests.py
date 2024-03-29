from django import test
from django.urls import reverse


class FrontTest(test.TestCase):
    def test_responses(self):
        """
        Testing of the front
        :return: None
        """
        # index
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

        # sitemap
        response = self.client.get(reverse("sitemap"))
        self.assertEqual(response.status_code, 200)

        # robots
        response = self.client.get(reverse("robots"))
        self.assertEqual(response.status_code, 200)

        # help
        response = self.client.get(reverse("help"))
        self.assertEqual(response.status_code, 200)

        # terms
        response = self.client.get(reverse("terms"))
        self.assertEqual(response.status_code, 200)

        # privacy
        response = self.client.get(reverse("privacy"))
        self.assertEqual(response.status_code, 200)
