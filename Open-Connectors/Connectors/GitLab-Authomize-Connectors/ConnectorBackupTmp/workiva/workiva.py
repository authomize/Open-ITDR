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


CONNECTOR_ID = "Workiva"

_API_OAUTH_TOKEN = "https://api.app.wdesk.com/iam/v1/oauth2/token"
_API_ORG_USERS = "https://api.app.wdesk.com/admin/v1/organizations/{}/orgReportUsers"  # noqa

# https://support.workiva.com/hc/en-us/articles/360036002431-Workspace-Roles
_ROLE_MAP = {
    "Copy Manager": AccessTypes.Write,
    "Editor": AccessTypes.Write,
    "Filing": AccessTypes.Write,
    "Org Security Admin": AccessTypes.Administrative,
    "Org User Admin": AccessTypes.Administrative,
    "Org Workspace Admin": AccessTypes.Administrative,
    "Viewer": AccessTypes.Read,
    "Workspace Owner": AccessTypes.Owner,
    "Workspace Support User": AccessTypes.Write,
    "XBRL Manager": AccessTypes.Write,
}


class Connector(Base):
    """Authomize Connector for Workiva.

    https://developers.workiva.com/workiva-admin/reference/admin-overview
    """

    def __init__(self):
        super().__init__(CONNECTOR_ID)
        self.org_id = os.environ["WORKIVA_ORG_ID"]
        client_id = os.environ["WORKIVA_CLIENT_ID"]
        client_secret = os.environ["WORKIVA_CLIENT_SECRET"]
        oauth2client = OAuth2Client(
            token_endpoint=_API_OAUTH_TOKEN,
            auth=(client_id, client_secret))
        self.auth = OAuth2ClientCredentialsAuth(oauth2client, scope="scim|r")

    def collect(self) -> dict:
        """Implement Base.collect()."""
        identity, access, asset = self._map_users(self._list_users())
        result = {}
        result[Base.IDENTITY] = identity
        result[Base.ACCESS] = access
        workiva_org = AssetDescription(
                id=self.org_id,
                name="Workiva Organization",
                type=AssetTypes.Application)
        result[Base.ASSET] = [workiva_org] + asset
        return result

    def _list_users(self):
        """Iterate over user accounts."""
        url = _API_ORG_USERS.format(os.environ["WORKIVA_ORG_ID"])
        data = []
        while url or data:
            if data:
                yield data.pop(0)
            else:
                res = requests.get(url, auth=self.auth)
                res.raise_for_status()
                body = res.json()
                data = body.get("data", [])
                links = body.get("links", {})
                url = links.get("next")

    def _map_users(self, users):
        """Map Workiva users to Authomize objects.

        Returns a tuple of three lists containing IdentityDescription,
        AccessDescription and AssetDescription objects.
        """
        identity = []
        access = []
        asset = []
        workspaces = {}
        for user in users:
            user_type = user["type"]
            if user_type != "orgReportUser":
                raise Exception(f"Unexpected user type: {user_type}")
            attr = user["attributes"]
            # Map user identity
            identity.append(IdentityDescription(
                id=user["id"],
                name=attr["displayName"],
                type=IdentityTypes.User,
                email=attr["email"],
                firstName=attr["firstName"],
                lastName=attr["lastName"],
                userName=attr["userName"],
                status=UserStatus.Enabled if attr.get("active") else UserStatus.Disabled  # noqa
            ))
            # Map organization roles
            for role in attr.get("organizationRoles", []):
                access.append(AccessDescription(
                    fromIdentityId=user["id"],
                    toAssetId=self.org_id,
                    accessType=_ROLE_MAP[role],
                    accessName=role))
            # Map workspace roles and collect workspaces
            memberships = attr.get("workspaceMemberships") or []
            for membership in memberships:
                workspace_id = membership["id"]
                workspace_name = membership["workspaceName"]
                workspaces[workspace_id] = workspace_name
                for role in membership.get("workspaceRoles", []):
                    access.append(AccessDescription(
                        fromIdentityId=user["id"],
                        toAssetId=workspace_id,
                        accessType=_ROLE_MAP[role],
                        accessName=role))
        # Map workspaces
        for workspace_id, workspace_name in workspaces.items():
            asset.append(AssetDescription(
                id=workspace_id,
                name=f"Workiva Workspace: {workspace_name}",
                type=AssetTypes.Workspace))
        return identity, access, asset
