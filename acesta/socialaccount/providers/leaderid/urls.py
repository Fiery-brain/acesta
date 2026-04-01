from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns

from acesta.socialaccount.providers.leaderid.provider import LeaderIDProvider


urlpatterns = default_urlpatterns(LeaderIDProvider)
