import os

from authomize.rest_api_client import (
    AccessDescription,
    AccessTypes,
    AssetDescription,
    AssetTypes,
    IdentityDescription,
    IdentityTypes,
    UserStatus,
)
import requests
from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth

from connectors import Base


CONNECTOR_ID = "Coupa"

_API_OAUTH_TOKEN = "https://gitlab.coupahost.com/oauth2/token"
_API_USERS = "https://gitlab.coupahost.com/api/users"

_ASSET_ID = 1


class Connector(Base):
    """Authomize Connector for Coupa.

    https://success.coupa.com/Integrate/Technical_Documentation/API
    """

    def __init__(self):
        super().__init__(CONNECTOR_ID)
        client_id = os.environ["COUPA_CLIENT_ID"]
        client_secret = os.environ["COUPA_CLIENT_SECRET"]
        oauth2client = OAuth2Client(
            token_endpoint=_API_OAUTH_TOKEN,
            auth=(client_id, client_secret))
        self.auth = OAuth2ClientCredentialsAuth(
            oauth2client,
            scope="core.user.read")

    def collect(self) -> dict:
        """Implement Base.collect()."""
        identity, access = self._map_users(self._list_users())
        result = {}
        result[Base.IDENTITY] = identity
        result[Base.ACCESS] = access
        coupa_asset = AssetDescription(
                id=_ASSET_ID,
                name="Coupa",
                type=AssetTypes.Application)
        result[Base.ASSET] = [coupa_asset]
        return result

    def _list_users(self):
        """Iterate over user accounts."""
        headers = {"Accept": "application/json"}
        data = []
        offset = 0
        while True:
            if data:
                yield data.pop(0)
            else:
                params = {"offset": offset}
                res = requests.get(
                    _API_USERS,
                    auth=self.auth,
                    headers=headers,
                    params=params)
                res.raise_for_status()
                data = res.json()
                if not data:
                    break
                offset += 50

    def _map_users(self, users):
        """Map Coupa users to Authomize objects.

        Returns a tuple of two lists containing IdentityDescription and
        AccessDescription objects.
        """
        known_ids = set()
        identity = []
        access = []
        for user in users:
            # Ignore Coupa Supplier Portal accounts
            if is_supplier(user):
                continue
            # Ignore duplicate IDs
            user_id = user["id"]
            if user_id in known_ids:
                continue
            else:
                known_ids.add(user_id)
            # Map user identity
            identity.append(IdentityDescription(
                id=user_id,
                name=user["fullname"],
                type=IdentityTypes.User,
                email=user["email"],
                firstName=user["firstname"],
                lastName=user["lastname"],
                userName=user["login"],
                status=UserStatus.Enabled if user.get("active") else UserStatus.Disabled  # noqa
            ))
            # Map roles
            for role in user.get("roles", []):
                access.append(AccessDescription(
                    fromIdentityId=user["id"],
                    toAssetId=_ASSET_ID,
                    accessType=AccessTypes.Unknown.value,
                    accessName=role["name"]))
        return identity, access


def is_supplier(user):
    """Return True if the user has only "Supplier" and "CSP ..." roles."""
    roles = [r["name"] for r in user.get("roles", [])]
    if roles and all(map(lambda r: r == "Supplier" or r.startswith("CSP "), roles)):  # noqa
        return True
    else:
        return False
