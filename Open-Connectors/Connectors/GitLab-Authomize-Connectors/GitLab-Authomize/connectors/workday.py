"""Authomize connector for Workday"""
import os
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth

from authomize.rest_api_client import (
    AccessDescription,
    AccessTypes,
    AssetDescription,
    AssetTypes,
    IdentityDescription,
    IdentityTypes,
    UserStatus
)

from connectors import Base

# Name of connector as seen in the Authomize UI
CONNECTOR_ID = "Workday"

# Arbitrary asset ID for the Workday application
_ASSET_ID = 3000

class Connector(Base):
    """
    Authomize connector for Workday
    """

    def __init__(self) -> None:
        super().__init__(CONNECTOR_ID)
        base_url = os.environ["WORKDAY_BASE_URL"]
        tenant_name = os.environ["WORKDAY_TENANT_NAME"]
        raas_name = os.environ["WORKDAY_RAAS_NAME"]
        client_id = os.environ["WORKDAY_RAAS_CLIENT_ID"]
        client_secret = os.environ["WORKDAY_RAAS_CLIENT_SECRET"]
        self.raas_url = f"{base_url}/ccx/service/customreport2/{tenant_name}/{client_id}/{raas_name}?format=json"
        self.auth = HTTPBasicAuth(client_id, client_secret)

    def collect(self) -> dict:
        """Implement Base.collect()."""
        identity, access = self._map_users(self._get_team_members(self.raas_url))
        result = {}
        result[Base.IDENTITY] = identity
        result[Base.ACCESS] = access
        workday_asset = AssetDescription(
                id=_ASSET_ID,
                name="Workday",
                type=AssetTypes.Application,
                href=
                "https://www.workday.com/en-us/products/human-capital-management/overview.html",)
        result[Base.ASSET] = [workday_asset]
        return result

    def _map_users(self, users: list) -> tuple([list, list]):
        """Map Workday users to Authomize objects.

        Returns a tuple of two lists containing IdentityDescription and
        AccessDescription objects.
        """
        identity = []
        access = []
        for user in users:
            # Map user identity
            identity.append(IdentityDescription(
                id=user["Employee_ID"],
                name=user.get("name", ""),
                firstName=user.get("firstname", ""),
                lastName=user.get("lastname", ""),
                type=IdentityTypes.User,
                email=user["email"],
                manager=user["manager"],
                title=user["title"],
                department=user["department"],
                createdAt=_to_datetime(user.get("hireDate", "")),
                terminationDate=_to_datetime(user.get("terminationDate", "")),
                status=_user_status(user),
            ))
            # Map roles
            for role in user.get("Role_group", []):
                access.append(AccessDescription(
                    fromIdentityId=user["Employee_ID"],
                    toAssetId=_ASSET_ID,
                    accessType=AccessTypes.Unknown.value,
                    accessName=role["Role"]
                ))
        return identity, access

    def _get_team_members(self, url) -> list:
        """Get Workday team member records."""
        headers = {"Accept": "application/json"}
        team_members_request = requests.get(
            url,
            auth = self.auth,
            headers=headers)
        team_members_request.raise_for_status()
        return team_members_request.json()["Report_Entry"]


def _user_status(user: dict) -> UserStatus:
    if user["status"] == "Active":
        return UserStatus.Enabled
    return UserStatus.Disabled

def _to_datetime(user_date: str) -> datetime:
    try:
        return datetime.strptime(user_date, '%Y-%m-%d')
    except ValueError:
        return None
