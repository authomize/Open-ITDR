"""Authomize connector for Xactly Incent"""
import os

import requests
from authomize.rest_api_client.generated.schemas import (
    AccessTypes,
    AssetTypes,
    UserStatus,
)
from authomize.rest_api_client import (
    AccessDescription,
    AssetDescription,
    IdentityDescription,
    IdentitiesInheritance,
    IdentityTypes,
)

from connectors import Base, retry_request

CONNECTOR_ID = "XactlyIncent"

# Arbitrary asset ID for the Xactly Incent application
_ASSET_ID = 10011

_API_HOST = "https://api.xactlycorp.com/api"
_USER_QUERY = """
SELECT xc_user.user_id,
       lower(xc_user.email) as email,
       xc_user.name,
       xc_user.enabled,
       xc_role.role_id,
       xc_role.name AS role_name,
       xc_role.is_active AS role_enabled,
       xc_role.descr AS role_description,
       xc_role.role_type
FROM xactly.xc_user
LEFT JOIN xactly.xc_user_role
ON xactly.xc_user.user_id = xactly.xc_user_role.user_id
LEFT JOIN xactly.xc_role
ON xactly.xc_role.role_id = xactly.xc_user_role.role_id
ORDER BY lower(email);
"""


def _user_to_dict(user: list) -> dict:
    """Map row fields to the column names"""
    return {
        "id": user[0],
        "email": user[1],
        "name": user[2],
        "enabled": user[3],
        "role_id": user[4],
        "role_name": user[5],
        "role_enabled": user[6],
        "role_description": user[7] or "",
        "role_type": user[8],
    }


class Connector(Base):
    """Authomize connector for Xactly Incent"""

    def __init__(self) -> None:
        self.token = ""
        self.roles = set()
        self.users = set()
        self.results = {}
        self.request_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        super().__init__(CONNECTOR_ID)

    def collect(self) -> dict:
        self.results = {
            self.ACCESS: [],
            self.IDENTITY: [],
            self.INHERITANCE_IDENTITY: [],
            self.ASSET: [],
            self.INHERITANCE_ASSET: [],
        }
        self._authenticate()
        self._populate_assets()
        self._populate_identities()
        return self.results

    @retry_request()
    def _authenticate(self) -> None:
        """Obtain a bearer token from Xactly and add it to the request headers."""
        client_id = os.environ["XACTLY_INCENT_CLIENT_ID"]
        consumer = os.environ["XACTLY_INCENT_CONSUMER"]
        data = {
            "username": os.environ["XACTLY_INCENT_USERNAME"],
            "password": os.environ["XACTLY_INCENT_PASSWORD"],
        }
        url = f"{_API_HOST}/oauth2/token?client_id={client_id}&consumer={consumer}&api=connect"

        response = requests.post(url, headers=self.request_headers, json=data)
        response.raise_for_status()
        token = response.json()["access_token"]
        self.request_headers["Authorization"] = f"Bearer {token}"

    def _populate_assets(self) -> None:
        self.results[self.ASSET] = [
            AssetDescription(
                id=_ASSET_ID,
                name="Xactly Incent",
                type=AssetTypes.Application,
                href="https://www.xactlycorp.com/products/incentive-compensation-management-software",
            )
        ]

    def _populate_identities(self) -> None:
        payload = {"command": _USER_QUERY, "defaultSchema": "xactly"}
        response = requests.post(
            f"{_API_HOST}/connect/v1/xdbc/execute",
            headers=self.request_headers,
            json=payload,
        )
        response.raise_for_status()
        data_url = response.headers["Location"]

        params = {"start": 0, "size": 100}
        while True:
            res = requests.get(
                f"{_API_HOST}{data_url}", headers=self.request_headers, params=params
            )
            res.raise_for_status()
            data = res.json()["data"]

            for user in data["rows"]:
                user_dict = _user_to_dict(user)
                self._populate_identity(user_dict)

            if data["totalRows"] <= params["start"] + params["size"]:
                break
            params["start"] += params["size"]

    def _populate_identity(self, user: dict) -> None:
        # Users might be in more than one role
        if user["id"] not in self.users:
            self.users.add(user["id"])
            id_desc = IdentityDescription(
                id=user["id"],
                email=user["email"],
                name=user["name"],
                status=_user_status(user["enabled"]),
                type=IdentityTypes.User.value,
            )
            self.results[self.IDENTITY].append(id_desc)

        inherited = IdentitiesInheritance(toId=user["role_id"], fromId=user["id"])
        self.results[self.INHERITANCE_IDENTITY].append(inherited)
        self._populate_role(user)

    def _populate_role(self, user: dict) -> None:
        if user["role_id"] in self.roles:
            return
        self.roles.add(user["role_id"])
        role = IdentityDescription(
            id=user["role_id"],
            name=user["role_name"],
            description=f"Role Type: {user['role_type']}",
            status=_user_status(user["role_enabled"]),
            type=IdentityTypes.Group.value,
        )
        self.results[self.IDENTITY].append(role)

        self.results[self.ACCESS].append(
            AccessDescription(
                fromIdentityId=user["role_id"],
                toAssetId=_ASSET_ID,
                accessType=AccessTypes.Unknown.value,
                accessName=user["role_name"],
            )
        )


def _user_status(status: str) -> UserStatus:
    if status == "1":
        return UserStatus.Enabled
    return UserStatus.Disabled
