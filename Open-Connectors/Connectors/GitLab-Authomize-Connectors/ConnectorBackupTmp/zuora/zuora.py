"""Authomize connector for Zuora"""
import csv
import os
import io
import re
import time
import zipfile
from datetime import datetime
from typing import Dict, Any

import requests
from authomize.rest_api_client.generated.connectors_rest_api.schemas import (
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

from connectors import Base
from logger import logger as log

CONNECTOR_ID = "Zuora"

_UI_HOST = "https://www.zuora.com"
_API_HOST = "https://rest.zuora.com"
_ASSETS = {
    "Zuora Billing": 99301,
    "Zuora Commerce": 99302,
    "Zuora Finance": 99303,
    "Zuora Payment": 99304,
    "Zuora Platform": 99305,
    "Zuora Reporting": 99306,
    "Zuora Revenue": 99307,
}

# Max number of times to check if export has completed
_EXPORT_ATTEMPTS = 10

# Number of seconds to wait between checking export status
_EXPORT_WAIT_INTERVAL = 5


def _get_bearer_token() -> str:
    data = {
        "client_id": os.environ["ZUORA_CLIENT_ID"],
        "client_secret": os.environ["ZUORA_CLIENT_SECRET"],
        "grant_type": "client_credentials",
    }

    response = requests.post(f"{_API_HOST}/oauth/token", data=data)
    return response.json()["access_token"]


class Connector(Base):
    """Authomize connector for Zuora"""

    _export_payload = "csrfToken={}&ExportData=Users&GroupBy=ACCOUNT&_Filter_Value_[3]=4&_Filter_Field_[2]=undefined&_Filter_Operator_[2]=None"

    def __init__(self) -> None:
        self.session = requests.Session()
        self.token = ""
        self.billing_roles = {}
        self.revenue_users = set()
        self.revenue_roles = set()
        self.results: Dict[str, list]
        self.current_time = datetime.utcnow()
        super().__init__(CONNECTOR_ID)

    def collect(self) -> dict:
        self.initialize_session()
        self.results = {
            self.ACCESS: [],
            self.IDENTITY: [],
            self.INHERITANCE_IDENTITY: [],
            self.ASSET: [],
            self.INHERITANCE_ASSET: [],
        }
        self._populate_assets()

        # Identities must be called first since it generates the unique list of groups
        # used to build the list of  AccessDescription objects
        self._populate_billing_identities()
        self._populate_billing_access()

        self._populate_revenue_identities()
        self._populate_revenue_access()

        return self.results

    def initialize_session(self) -> None:
        """Exchange bearer token for session cookie.

        Since we are communicating directly with the Web application, we need to to instantiate
        a session to call the web application methods. This authentication flow was determined
        by using Burpsuite to uncover undocumented APIs and web app functionality."""
        log.debug("initialize zuora session", extra={"connector": self.connector_name})
        self.token = _get_bearer_token()

        # Get ZSession cookie for billing
        # This session is used to interact with the web application.
        # Then bearer token does not work for all endpoints.
        resp = self.session.get(
            f"{_UI_HOST}/platform/api/zsession-refresh",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        resp.raise_for_status()

        # Populate other cookies by requesting root of the web application.
        # These cookies contain user details that are needed to successfully obtain
        # The session cookie for Zuora revenue.
        resp = self.session.get(f"{_UI_HOST}/platform/webapp")
        resp.raise_for_status()

        # Get ZR-LOGIN-RPRO cookie for revenue
        resp = self.session.get(
            f"{_UI_HOST}/revpro/api/revpro/public/oauth/validatetoken"
        )
        resp.raise_for_status()

    def _populate_assets(self) -> None:
        for asset_name, asset_id in _ASSETS.items():
            self.results[self.ASSET].append(
                AssetDescription(
                    id=asset_id,
                    name=asset_name,
                    type=AssetTypes.Application,
                    href=_UI_HOST,
                )
            )

    def _populate_billing_identities(self) -> None:
        extra = {"connector": self.connector_name}
        log.debug("export all billing users", extra=extra)
        export_id = self._export_billing_users()

        extra["export_id"] = export_id
        log.debug("download export", extra=extra)
        export_data = self._download_billing_export(export_id)

        log.debug("delete export", extra=extra)
        self._delete_billing_export(export_id)

        for user in export_data:
            self._populate_billing_identity(user)

    def _export_billing_users(self) -> str:
        response = self.session.post(
            f"{_UI_HOST}/apps/ExpFile.do",
            params={"method": "ajaxExport"},
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
            },
            data=self._export_payload.format(self._expfile_csrf_token()),
        )

        export_id_search = re.search(
            r"cancelExportFile\('([0-9a-f]{32})'", response.text
        )
        if export_id_search:
            return export_id_search.group(1)
        raise Exception("cannot find export file ID")

    def _expfile_csrf_token(self) -> str:
        response = self.session.get(
            f"{_UI_HOST}/apps/ExpFile.do", params={"method": "searchView"}
        )
        csrf_search = re.search('csrf="(.*)"', response.text, re.IGNORECASE)
        if csrf_search:
            return csrf_search.group(1).replace("=", "%3D")
        raise Exception("unable to obtain CSRF token")

    def _download_billing_export(self, export_id: str) -> Dict[str, Any]:
        # first extract the download ID
        i = 0
        download_id = ""
        while i < _EXPORT_ATTEMPTS:
            time.sleep(_EXPORT_WAIT_INTERVAL)
            response = self.session.get(
                f"{_UI_HOST}/apps/ExpFile.do", params={"method": "searchView"}
            )
            re_tmpl = r"downloadExportedFile\('([0-9a-f]{32}).*(?=%s)"
            download_id_re = re.compile(re_tmpl % export_id)
            view_content = response.text.replace("\n", " ")
            match = download_id_re.search(view_content)
            if match:
                download_id = match.group(1)
                break
            i += 1

        if download_id == "":
            raise Exception("Could not determine export download ID")

        # Use download_id to obtain zip file of user export
        response = requests.get(
            f"{_API_HOST}/v1/files/{download_id}",
            headers={"Authorization": f"Bearer {self.token}"},
        )

        # unzip CSV and convert to dictionary
        zip_bytes = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_bytes) as input_zip:
            data = input_zip.read("AllUsersList.csv")
            decoded_data = csv.DictReader(io.StringIO(data.decode()))
        return list(decoded_data)

    def _delete_billing_export(self, export_id: str) -> None:
        response = self.session.post(
            f"{_UI_HOST}/apps/ExpFile.do",
            params={
                "method": "ajaxDeleteExport",
                "exportFileId": export_id,
                "csrfToken": self._expfile_csrf_token(),
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
            },
            data=self._export_payload.format(self._expfile_csrf_token()),
        )

        response.raise_for_status()

    def _populate_billing_identity(self, user: dict) -> None:
        id_desc = IdentityDescription(
            id=user["User ID"],
            userName=user.get("User Name", ""),
            firstName=user.get("First Name", ""),
            lastName=user.get("last Name", ""),
            type=IdentityTypes.User.value,
            email=user["Work Email"],
            status=_billing_user_status(user),
        )
        try:
            id_desc.lastLoginDate = datetime.strptime(user["Last Login"], "%m/%d/%Y")
        except ValueError:
            pass
        self.results[self.IDENTITY].append(id_desc)

        for asset_name, asset_id in _ASSETS.items():
            user_role = user.get(f"{asset_name} Role")
            # prepend asset ID to role name in case multiple assets have the same role name
            role_id = f"{asset_id} {user_role}"

            if not user_role:
                continue

            inherited = IdentitiesInheritance(toId=role_id, fromId=user["User ID"])
            self.results[self.INHERITANCE_IDENTITY].append(inherited)

            if role_id in self.billing_roles:
                continue

            role = IdentityDescription(
                id=role_id,
                name=user_role,
                type=IdentityTypes.Group.value,
            )
            self.results[self.IDENTITY].append(role)
            self.billing_roles[role_id] = (user_role, asset_id)

    def _populate_billing_access(self) -> None:
        for role_id, role_details in self.billing_roles.items():
            self.results[self.ACCESS].append(
                AccessDescription(
                    fromIdentityId=role_id,
                    toAssetId=role_details[1],
                    accessType=AccessTypes.Unknown.value,
                    accessName=role_details[0],
                )
            )

    def _populate_revenue_identities(self) -> None:
        # This payload was determined by using Burpsuite to reverse-engineer the web application.
        # Use "User Assignment Report - Custom" layout
        payload = {"report": {"rep_id": "67", "layout_id": "10058", "p_filters": []}}
        response = self.session.post(
            f"{_UI_HOST}/revpro/api/revpro/secure/runReports/runReport", json=payload
        )
        response.raise_for_status()
        users = []

        for user in response.json()["data"]:
            # These labels are determined by running the POST request above against
            #    /revpro/api/revpro/secure/runReports/runReportLabels
            user_record = {
                # There is no user ID returned from revpro, so using username as ID
                "id": user["A17684"],
                "user_name": user["A17684"],
                "full_name": user["A17685"],
                "email": user["A17686"],
                "effectivity_start": user["A17687"],
                "effectivity_end": user.get("A17688", None),
                "role": user["A17690"],
                "role_enabled": user["A17692"],
                "role_effectivity_start": user["A17695"],
                "role_effectivity_end": user.get("A17696", None),
            }

            users.append(user_record)

        for user in users:
            self._populate_revenue_identity(user)

    def _populate_revenue_identity(self, user: dict) -> None:
        if user["id"] not in self.revenue_users:
            self.results[self.IDENTITY].append(
                IdentityDescription(
                    id=user["user_name"],
                    email=user["email"],
                    userName=user["user_name"],
                    name=user["full_name"],
                    status=self._revenue_user_status(user),
                    type=IdentityTypes.User.value,
                )
            )
            self.revenue_users.add(user["id"])

        if self._revenue_user_role_status(user) == UserStatus.Enabled:
            inherited = IdentitiesInheritance(toId=user["role"], fromId=user["user_name"])
            self.results[self.INHERITANCE_IDENTITY].append(inherited)

        if user["role"] not in self.revenue_roles:
            self.results[self.IDENTITY].append(
                IdentityDescription(
                    id=user["role"],
                    name=user["role"],
                    type=IdentityTypes.Group.value,
                    status=_revenue_role_status(user["role_enabled"]),
                )
            )
            self.revenue_roles.add(user["role"])

    def _populate_revenue_access(self) -> None:
        for role in self.revenue_roles:
            self.results[self.ACCESS].append(
                AccessDescription(
                    fromIdentityId=role,
                    toAssetId=_ASSETS["Zuora Revenue"],
                    accessType=AccessTypes.Unknown.value,
                    accessName=role,
                )
            )

    def _revenue_user_status(self, user: dict) -> UserStatus:
        status_keys = ["effectivity_end", "effectivity_start"]
        return self._check_revenue_status(user, status_keys)

    def _revenue_user_role_status(self, user: dict) -> UserStatus:
        status_keys = ["role_effectivity_end", "role_effectivity_start"]
        return self._check_revenue_status(user, status_keys)

    def _check_revenue_status(self, user: dict, status_keys: list) -> UserStatus:
        def is_valid_time(key: str) -> bool:
            valid = True
            if not user[key]:
                return valid
            key_time = datetime.fromisoformat(user[key].rstrip("Z"))
            direction = key.split("_")[-1]
            if direction == "end":
                valid = key_time > self.current_time
            elif direction == "start":
                valid = key_time < self.current_time
            return valid

        status = UserStatus.Enabled

        for key in status_keys:
            if not is_valid_time(key):
                status = UserStatus.Disabled
                break

        return status


def _billing_user_status(user: dict) -> UserStatus:
    if user["Status"] == "Active":
        return UserStatus.Enabled
    return UserStatus.Disabled


def _revenue_role_status(status: str) -> UserStatus:
    if status.lower() == "yes":
        return UserStatus.Enabled
    return UserStatus.Disabled
