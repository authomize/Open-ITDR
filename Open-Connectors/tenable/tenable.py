"""Authomize connector for Tenable"""
import os
from typing import Any, Dict, List

from tenable.io import TenableIO

from authomize.rest_api_client.generated.schemas import (
    AccessTypes,
    AssetTypes,
    UserStatus,
)
from authomize.rest_api_client import (
    AccessDescription,
    AssetDescription,
    IdentityDescription,
    IdentityTypes,
)

from connectors import Base

# Name of connector as seen in the Authomize UI
CONNECTOR_ID = "TenableIO"

# Arbitrary asset ID for the TenableIO application
_ASSET_ID = 10001

# https://developer.tenable.com/docs/permissions#user-roles
_role_mappings = {
    0: {"name": "No Access", "type": AccessTypes.Read.value},
    16: {"name": "Basic", "type": AccessTypes.Read.value},
    24: {"name": "Scan Operator", "type": AccessTypes.Execute.value},
    32: {"name": "Standard", "type": AccessTypes.Create.value},
    40: {"name": "Scan Manager", "type": AccessTypes.Create.value},
    64: {"name": "Administrator", "type": AccessTypes.Administrative.value},
}


class Connector(Base):
    """Authomize connector for Tenable"""

    def __init__(self) -> None:
        self.client = TenableIO(
            os.environ["TENABLE_ACCESS_KEY"], os.environ["TENABLE_SECRET_KEY"]
        )
        super().__init__(CONNECTOR_ID)

    def collect(self) -> dict:
        bundle = self._get_users()
        bundle[self.ASSET] = [
            AssetDescription(
                id=_ASSET_ID,
                name="TenableIO",
                type=AssetTypes.Application,
                href="https://cloud.tenable.com",
            )
        ]
        return bundle

    def _get_users(self) -> Dict[str, List[IdentityDescription]]:
        users: Dict[str, List[Any]] = {self.ACCESS: [], self.IDENTITY: []}
        for user in self.client.users.list():
            users[self.IDENTITY].append(_identity_description(user))
            users[self.ACCESS].append(_access_description(user))
        return users


def _access_description(user: dict) -> AccessDescription:
    return AccessDescription(
        fromIdentityId=user["id"],
        toAssetId=_ASSET_ID,
        accessType=_role_mappings[user["permissions"]]["type"],
        accessName=_role_mappings[user["permissions"]]["name"],
    )


def _identity_description(user: dict) -> IdentityDescription:
    # A user name is not nescesarily returned from tenable
    return IdentityDescription(
        id=user["id"],
        name=user.get("name", ""),
        type=IdentityTypes.User.value,
        email=user["email"],
        userName=user["user_name"],
        status=_user_status(user),
        hasTwoFactorAuthenticationEnabled=_user_has_two_factor(user),
    )


def _user_status(user: dict) -> UserStatus:
    if user["enabled"]:
        return UserStatus.Enabled
    return UserStatus.Disabled


def _user_has_two_factor(user: dict) -> bool:
    if user.get("two_factor"):
        return True
    return False
