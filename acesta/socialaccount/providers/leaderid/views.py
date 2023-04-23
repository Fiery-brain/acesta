import requests
from allauth.socialaccount.providers.oauth2.views import OAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView
from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView

from .provider import LeaderIDProvider


class LeaderIDAuth2Adapter(OAuth2Adapter):
    provider_id = LeaderIDProvider.id
    access_token_url = "https://leader-id.ru/oauth/access_token"
    authorize_url = "https://leader-id.ru/oauth/authorize"
    profile_url = "https://leader-id.ru/api/users"

    def complete_login(self, request, app, token, **kwargs):
        resp = requests.get(
            f"{self.profile_url}/{kwargs.get('response').get('user_id')}",
            params={"access_token": token.token, "format": "json"},
        )
        resp.raise_for_status()
        extra_data = resp.json()
        return self.get_provider().sociallogin_from_response(request, extra_data)


oauth2_login = OAuth2LoginView.adapter_view(LeaderIDAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(LeaderIDAuth2Adapter)
