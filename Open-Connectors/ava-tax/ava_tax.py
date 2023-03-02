"""Authomize connector for Avalara"""
import os
from typing import Any, Dict, List

from avalara import AvataxClient
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
CONNECTOR_ID = "AvaTax"

# Arbitrary asset ID for the AvaTax application
_ASSET_ID = 10000

# The only roles currently in use in Avalara are AccountAdmin and AccountUser
# TODO: figure out what the role mappings should be
_role_type_mappings = {
    # "NoAccess": None,
    # "SiteAdmin": AccessTypes.Administrative,
    # "AccountOperator": None,
    "AccountAdmin": AccessTypes.Administrative.value,
    "AccountUser": AccessTypes.Write.value,
    # "SystemAdmin": None,
    # "Registrar": None,
    # "CSPTester": None,
    # "CSPAdmin": None,
    # "SystemOperator": None,
    # "TechnicalSupportUser": None,
    # "TechnicalSupportAdmin": None,
    # "TreasuryUser": None,
    # "TreasuryAdmin": None,
    # "ComplianceUser" "ComplianceAdmin": None,
    # "ProStoresOperator": None,
    # "CompanyUser": None,
    # "CompanyAdmin": None,
    # "Compliance Temp User": None,
    # "Compliance Root User": None,
    # "Compliance Operator": None,
    # "SSTAdmin": None,
    # "FirmUser": None,
    # "FirmAdmin": None,
}

# Can't find an API to return the ID to name mapping
# This was populated by matching what is displayed in the UI
# To the securityRoleId returned in the API request.
_role_name_mappings = {
    "AccountAdmin": "Account administrator",
    "AccountUser": "Limited access account user",
}


class Connector(Base):
    """Authomize connector for Avalara"""

    def __init__(self) -> None:
        self.client = AvataxClient("authomize-sync", "0.0", None, "production")
        self.client = self.client.add_credentials(
            os.environ["AVALARA_USERNAME"], os.environ["AVALARA_PASSWORD"]
        )
        super().__init__(CONNECTOR_ID)

    def collect(self) -> dict:
        bundle = self._get_users()
        bundle[self.ASSET] = [_asset_description()]
        return bundle

    def _get_users(self) -> Dict[str, List[IdentityDescription]]:
        user_response = self.client.query_users().json()
        users: Dict[str, List[Any]] = {self.ACCESS: [], self.IDENTITY: []}
        for user in user_response["value"]:
            users[self.IDENTITY].append(_identity_description(user))
            users[self.ACCESS].append(_access_description(user))
        return users


def _access_description(user: dict) -> AccessDescription:
    return AccessDescription(
        fromIdentityId=user["id"],
        toAssetId=_ASSET_ID,
        accessType=_role_type_mappings[user["securityRoleId"]],
        accessName=_role_name_mappings[user["securityRoleId"]],
    )


def _identity_description(user: dict) -> IdentityDescription:
    return IdentityDescription(
        id=user["id"],
        name=user["firstName"] + " " + user["lastName"],
        type=IdentityTypes.User.value,
        email=user["email"],
        firstName=user["firstName"],
        lastName=user["lastName"],
        userName=user["userName"],
        status=_user_status(user),
    )


def _asset_description() -> AssetDescription:
    return AssetDescription(
        id=_ASSET_ID,
        name="AvaTax",
        type=AssetTypes.Application,
        href="https://www.avalara.com",
    )


def _user_status(user: dict) -> UserStatus:
    if user["isActive"]:
        return UserStatus.Enabled
    return UserStatus.Disabled
