from acesta.user.models import User


class CredentialsMixin:
    """
    Setting credentials for tests
    """

    fixtures = ["acesta/" "geo/fixtures/region.yaml"]
    credentials = None

    def setUp(self):
        self.credentials = {
            "email": "test@ru.ru",
            "password": "secret",
        }
        User.objects.create_user(
            email=self.credentials["email"],
            username=self.credentials["email"],
            password=self.credentials["password"],
            registered=True,
            region_id="01",
        )
