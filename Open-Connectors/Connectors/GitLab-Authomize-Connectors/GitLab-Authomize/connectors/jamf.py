"""Authomize connector for Jamf"""
import os
import requests
from requests.auth import HTTPBasicAuth

from authomize.rest_api_client import (
    AccessDescription,
    AccessTypes,
    AssetDescription,
    AssetTypes,
    IdentityDescription,
    IdentityTypes,
)

from connectors import Base

# Name of connector as seen in the Authomize UI
CONNECTOR_ID = "Jamf"

_API_OAUTH_TOKEN = "https://gitlab.jamfcloud.com/api/v1/auth/token"
_API_USERS = "https://gitlab.jamfcloud.com/api/user"

# Arbitrary asset ID for the Jamf application
_ASSET_ID = 2


class Connector(Base):
    """
    Authomize connector for Jamf

    https://developer.jamf.com/jamf-pro/reference/get_user
    """

    def __init__(self) -> None:
        super().__init__(CONNECTOR_ID)
        client_id = os.environ["JAMF_USERNAME"]
        client_secret = os.environ["JAMF_PASSWORD"]
        self.auth = HTTPBasicAuth(client_id, client_secret)

    def collect(self) -> dict:
        """Implement Base.collect()."""
        identity, access = self._map_users(self._get_users())
        result = {}
        result[Base.IDENTITY] = identity
        result[Base.ACCESS] = access
        jamf_asset = AssetDescription(
                id=_ASSET_ID,
                name="Jamf",
                type=AssetTypes.Application,
                href="https://www.jamf.com/products/jamf-pro/",)
        result[Base.ASSET] = [jamf_asset]
        return result

    def _get_users(self) -> list:
        """Get user accounts."""
        access_token = self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        users_request = requests.get(
            _API_USERS,
            headers=headers)
        users_request.raise_for_status()
        users_data = users_request.json()
        return users_data

    def _map_users(self, users: list) -> tuple([list, list]):
        """Map Jamf users to Authomize objects.

        Returns a tuple of two lists containing IdentityDescription and
        AccessDescription objects.
        """
        identity = []
        access = []
        for user in users:
            user = _process_user(user)
            # Map user identity
            identity.append(IdentityDescription(
                id=user["id"],
                name=user["realName"],
                type=IdentityTypes.User,
                email=user["email"],
                userName=user["username"]
            ))
            # Map roles
            role = user.get("privilegeSet", None)
            access.append(AccessDescription(
                fromIdentityId=user["id"],
                toAssetId=_ASSET_ID,
                accessType=AccessTypes.Unknown.value,
                accessName=role
            ))
        return identity, access

    def _get_access_token(self) -> str:
        """Obtain a Bearer Token to use with other JAMF API endpoints"""
        access_data = []
        token_request = requests.post(
                    _API_OAUTH_TOKEN,
                    auth = self.auth)
        token_request.raise_for_status()
        access_data = token_request.json()
        return access_data["token"]

def _process_user(user_dict: dict) -> dict:
    """Set default value for realName and strip whitespace from strings"""
    if user_dict["realName"] is None:
        user_dict["realName"] = ""

    user_dict["email"] = user_dict["email"].strip()
    user_dict["realName"] = user_dict["realName"].strip()
    user_dict["username"] = user_dict["username"].strip()

    return user_dict
