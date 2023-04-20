"""Authomize connector for ZenDesk"""
import os
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth

from zenpy import Zenpy
from zenpy.lib.api_objects import User as ZDUser

from authomize.rest_api_client.generated.connectors_rest_api.schemas import (
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
CONNECTOR_ID = "ZenDesk"

# Arbitrary asset ID for the Workday application
_ASSET_ID = 70000

# The only roles currently in use in Avalara are AccountAdmin and AccountUser
# TODO: figure out what the role mappings should be
_role_type_mappings = {
    "end-user": AccessTypes.Use.value,
    "agent": AccessTypes.Administrative.value,
    "admin": AccessTypes.Owner.value
}

_role_name_mappings = {
    "end-user": "End User",
    "agent": "Agent",
    "admin": "Admin"
}

class Connector(Base):
    """
    Authomize connector for ZenDesk
    """

    def __init__(self) -> None:
        super().__init__(CONNECTOR_ID)
        self.subdomain = os.environ["ZENDESK_SUBDOMAIN"]
        credentials = {
            'email': os.environ["ZENDESK_EMAIL"],
            'token': os.environ["ZENDESK_TOKEN"],
            'subdomain': self.subdomain
        }
        self.zenpy_client = Zenpy(**credentials)

    def collect(self) -> dict:
        bundle = self._get_users()
        bundle[self.ASSET] = [_asset_description(self.subdomain)]
        return bundle

    def _get_users(self) -> tuple([list, list]):
        zd_users = self.zenpy_client.search_export(type='user')
        users: Dict[str, List[Any]] = {self.ACCESS: [], self.IDENTITY: []}
        for user in zd_users:
            users[self.IDENTITY].append(_identity_description(user))
            users[self.ACCESS].append(_access_description(user))
        return users

def _identity_description(user: ZDUser) -> IdentityDescription:
    return IdentityDescription(
        id=user.id,
        name=user.name,
        email=user.email,
        type=IdentityTypes.User.value,
        userType=user.role,
        #firstName='',
        #lastName='',
        userName=user.email,
        status=_user_status(user),
        href=user.url,
        createdAt=user.created_at,
        hasTwoFactorAuthenticationEnabled=user.two_factor_auth_enabled,
        lastLoginAt=user.last_login_at
    )

#global access permission to the application asset - not permissions inside
def _access_description(user: ZDUser) -> AccessDescription:
    return AccessDescription(
        fromIdentityId=user.id,
        toAssetId=_ASSET_ID,
        accessType=_role_type_mappings[user.role],
        accessName=_role_name_mappings[user.role],
    )


#used for the bundle, not indivdual user
def _asset_description(subdomain) -> AssetDescription:
    return AssetDescription(
        id=_ASSET_ID,
        name="ZenDesk",
        type=AssetTypes.Application,
        href="https://" + subdomain + ".zendesk.com",
    )


def _user_status(user: ZDUser) -> UserStatus:
    if user.suspended:
        return UserStatus.Suspended
    if user.active:
        return UserStatus.Enabled
    return UserStatus.Disabled
