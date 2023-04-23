from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class LeaderIDAccount(ProviderAccount):
    pass


class LeaderIDProvider(OAuth2Provider):
    id = "leaderid"
    name = "LeaderID"
    account_class = LeaderIDAccount

    def extract_uid(self, data):
        """Extract uid ('id') and ensure it's a str."""
        try:
            return str(data.get("Data").get("Id"))
        except AttributeError:
            return None

    def extract_common_fields(self, data):
        common_fields = {}
        user_data = data.get("Data")
        if user_data:
            common_fields.update(
                dict(
                    last_name=user_data.get("LastName"),
                    first_name=user_data.get("FirstName"),
                    middle_name=user_data.get("FatherName"),
                    phone=user_data.get("Phones")[0],
                    email=user_data.get("Email"),
                )
            )
            if "Work" in user_data.keys():
                common_fields.update(
                    dict(
                        position=user_data.get("Work").get("Position"),
                    )
                )
                if "Company" in user_data.get("Work").keys():
                    common_fields.update(
                        dict(
                            company=user_data.get("Work").get("Company").get("Name"),
                        )
                    )
            if "Address" in user_data.keys():
                common_fields.update(
                    dict(
                        region=user_data.get("Address").get("Region"),
                        city=user_data.get("Address").get("City"),
                    )
                )
        return common_fields


provider_classes = [LeaderIDProvider]
