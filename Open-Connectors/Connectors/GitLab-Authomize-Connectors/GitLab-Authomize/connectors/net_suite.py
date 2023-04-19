"""Authomize connector for NetSuite"""
import os
from typing import Any, Dict, List

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
from netsuitesdk import NetSuiteConnection

from connectors import Base
from logger import logger as log

# Arbitrary Asset ID for the NetSuite applicaiton
_ASSET_ID = 1234
_CONNECTOR_ID = "NetSuite"

# This is the namespaced (the namespace is in brackets) search object necessary to run saved searches
# (which is necessary to get employees AND their roles). The namespace was discovered by using an
# http proxy (Charles/Burpsuite) and running the `netsuitesdk`'s `connector.employees.get_all()` call
# and then manually creating the request with the `netsuitesdk`.
_EMPLOYEE_SEARCH_ADVANCED = "{urn:employees_2019_1.lists.webservices.netsuite.com}EmployeeSearchAdvanced"

# These are retrieved from our NetSuite admin - Roles are not accessible via API
# There isn't an obvious mapping to the Authomize `AccessTypes` so setting them to unknown allows
# the Authomize UI to show the role as it's named in NetSuite
_NETSUITE_ROLE_MAP = {
    "1": { "name": "Accountant", "type": AccessTypes.Unknown.value },
    "2": { "name": "Accountant (Reviewer)", "type": AccessTypes.Unknown.value },
    "3": { "name": "Administrator", "type": AccessTypes.Unknown.value },
    "4": { "name": "A/P Clerk", "type": AccessTypes.Unknown.value },
    "5": { "name": "A/R Clerk", "type": AccessTypes.Unknown.value },
    "6": { "name": "Bookkeeper", "type": AccessTypes.Unknown.value },
    "7": { "name": "CEO(Hands Off)", "type": AccessTypes.Unknown.value },
    "8": { "name": "CEO", "type": AccessTypes.Unknown.value },
    "9": { "name": "Sales Manager", "type": AccessTypes.Unknown.value },
    "10": { "name": "Sales Person", "type": AccessTypes.Unknown.value },
    "11": { "name": "Store Manager", "type": AccessTypes.Unknown.value },
    "14": { "name": "Customer Center", "type": AccessTypes.Unknown.value },
    "15": { "name": "Employee Center", "type": AccessTypes.Unknown.value },
    "16": { "name": "Vendor Center", "type": AccessTypes.Unknown.value },
    "21": { "name": "Partner Center", "type": AccessTypes.Unknown.value },
    "22": { "name": "Intranet Manager", "type": AccessTypes.Unknown.value },
    "25": { "name": "System Administrator", "type": AccessTypes.Unknown.value },
    "26": { "name": "Sales Administrator", "type": AccessTypes.Unknown.value },
    "30": { "name": "Netsuite Support Center", "type": AccessTypes.Unknown.value }, #NOTE: This needs to be added manually, it doesn't appear in the list from NetSuite
    "41": { "name": "CFO", "type": AccessTypes.Unknown.value },
    "42": { "name": "Retail Clerk", "type": AccessTypes.Unknown.value },
    "43": { "name": "Retail Clerk (Web Services Only)", "type": AccessTypes.Unknown.value },
    "44": { "name": "Sales Vice President", "type": AccessTypes.Unknown.value },
    "48": { "name": "Human Resources Generalist", "type": AccessTypes.Unknown.value },
    "49": { "name": "Chief People Officer (CPO)", "type": AccessTypes.Unknown.value },
    "50": { "name": "Buyer", "type": AccessTypes.Unknown.value },
    "55": { "name": "Developer", "type": AccessTypes.Unknown.value },
    "57": { "name": "Data Warehouse Integrator", "type": AccessTypes.Unknown.value },
    "1000": { "name": "Tax Reporting CFO", "type": AccessTypes.Unknown.value },
    "1001": { "name": "Tax Reporting Accountant", "type": AccessTypes.Unknown.value },
    "1002": { "name": "Tax Reporting Accountant (Reviewer)", "type": AccessTypes.Unknown.value },
    "1003": { "name": "Tax Reporting Bookkeeper", "type": AccessTypes.Unknown.value },
    "1004": { "name": "Expensify Integration", "type": AccessTypes.Unknown.value },
    "1008": { "name": "Custom System Administrator", "type": AccessTypes.Unknown.value },
    "1009": { "name": "Custom Administrator Processes and System", "type": AccessTypes.Unknown.value },
    "1010": { "name": "Custom FPA ", "type": AccessTypes.Unknown.value },
    "1011": { "name": "Fixed Assets Management", "type": AccessTypes.Unknown.value },
    "1012": { "name": "Stitch", "type": AccessTypes.Unknown.value },
    "1013": { "name": "Custom Accountant - All Ledgers", "type": AccessTypes.Unknown.value },
    "1014": { "name": "Custom Accounts Payable", "type": AccessTypes.Unknown.value },
    "1015": { "name": "Custom Tax Accountant", "type": AccessTypes.Unknown.value },
    "1016": { "name": "FiveTran", "type": AccessTypes.Unknown.value },
    "1017": { "name": "BlackLine OneWorld Data Connect Role", "type": AccessTypes.Unknown.value },
    "1018": { "name": "BlackLine Data Connect Role", "type": AccessTypes.Unknown.value },
    "1019": { "name": "BlackLine OneWorld Data Connect DataWriter Role", "type": AccessTypes.Unknown.value },
    "1020": { "name": "BlackLine Data Connect DataWriter Role", "type": AccessTypes.Unknown.value },
    "1021": { "name": "BambooHR Custom OneWorld Web Services", "type": AccessTypes.Unknown.value },
    "1022": { "name": "Custom Auditor (read only)", "type": AccessTypes.Unknown.value },
    "1023": { "name": "Custom IC AR and AP", "type": AccessTypes.Unknown.value },
    "1024": { "name": "Custom Auditor BV (read only)", "type": AccessTypes.Unknown.value },
    "1025": { "name": "Custom Buyer", "type": AccessTypes.Unknown.value },
    "1026": { "name": "Custom A/P Clerk Montpac All Entities Edit", "type": AccessTypes.Unknown.value },
    "1027": { "name": "Custom A/P Clerk Excluding Federal and View Only", "type": AccessTypes.Unknown.value },
    "1028": { "name": "Tipalti Integration Role", "type": AccessTypes.Unknown.value },
    "1029": { "name": "FloQast Integration ", "type": AccessTypes.Unknown.value },
    "1030": { "name": "Custom Accountant - All Ledgers (For Testing)", "type": AccessTypes.Unknown.value },
    "1031": { "name": "Adaptive Insights Integration", "type": AccessTypes.Unknown.value },
    "1032": { "name": "Gitlab - Accounting Ops", "type": AccessTypes.Unknown.value },
    "1033": { "name": "GitLab IT Administrator", "type": AccessTypes.Unknown.value },
    "1034": { "name": "Custom Controller (Read Only)", "type": AccessTypes.Unknown.value },
    "1035": { "name": "GitLab Workday Integration", "type": AccessTypes.Unknown.value },
    "1036": { "name": "Custom Auditor (read only) OKTA TEST", "type": AccessTypes.Unknown.value },
    "1037": { "name": "GitLab Zuora Integrations", "type": AccessTypes.Unknown.value },
    "1038": { "name": "Gitlab IT Admin (External_NonSaml)", "type": AccessTypes.Unknown.value },
    "1039": { "name": "Custom EFT Role", "type": AccessTypes.Unknown.value },
    "1040": { "name": "Custom Auditor (read only & External_NonSaml)", "type": AccessTypes.Unknown.value },
    "1041": { "name": "Gitlab - AP Close Period", "type": AccessTypes.Unknown.value },
    "1042": { "name": "Custom A/P Clerk Montpac All Entities Edit_NonSAML", "type": AccessTypes.Unknown.value },
    "1043": { "name": "Gitlab Auditor - Authomize", "type": AccessTypes.Unknown.value },
    "1044": { "name": "NBS Registration Check", "type": AccessTypes.Unknown.value },
    "1045": { "name": "NBS Registration Entry", "type": AccessTypes.Unknown.value },
    "1046": { "name": "ABR Accounting Prefs/Company Info Role", "type": AccessTypes.Unknown.value },
    "1047": { "name": "ABR Scheduling Role", "type": AccessTypes.Unknown.value },
    "1048": { "name": "ABR Role", "type": AccessTypes.Unknown.value },
    "1149": { "name": "TripActions Integration Role", "type": AccessTypes.Unknown.value },
    "1249": { "name": "Zip Integration", "type": AccessTypes.Unknown.value },
}

# This is from our NetSuite admin
_SAVED_SEARCH_ID = 671

class Connector(Base):
    """Authomize connector for NetSuite"""

    def __init__(self):
        super().__init__(_CONNECTOR_ID)

    def collect(self) -> dict:
        self.conn = self._authenticate()

        if self.conn is None:
            raise Exception("Connection to NetSuite failed")

        bundle = self._get_users()
        bundle[self.ASSET] = [
            AssetDescription(
                id=_ASSET_ID,
                name="NetSuite",
                type=AssetTypes.Application,
                href="https://netsuite.com",
            )
        ]

        return bundle


    def _authenticate(self):
        account = os.getenv("NS_ACCOUNT")
        client_id = os.getenv("NS_CONSUMER_KEY")
        client_secret = os.getenv("NS_CONSUMER_SECRET")
        token_key = os.getenv("NS_TOKEN_KEY")
        token_secret = os.getenv("NS_TOKEN_SECRET")

        nc = NetSuiteConnection(
            account=account,
            consumer_key=client_id,
            consumer_secret=client_secret,
            token_key=token_key,
            token_secret=token_secret,
            caching=False # Don't create an SQLite DB file
        )

        return nc


    def _get_users(self):
        """Iterate over user accounts."""

        EmployeeSearchAdvanced = self.conn.client._client.get_type(_EMPLOYEE_SEARCH_ADVANCED)

        users: Dict[str, List[Any]] = {self.ACCESS: [], self.IDENTITY: []}
        unique_users = set()

        # The `netsuitesdk` doesn't expose the necessary SOAP methods/objects (and makes some assumptions on the search results)
        # that don't allow us to call the saved search directly without going through private members.
        results = self.conn.client.search(EmployeeSearchAdvanced(savedSearchId=_SAVED_SEARCH_ID))
        currentPage = 1
        totalPages = results.totalPages
        searchId = results.searchId

        while True:
            for user in results.searchRowList.searchRow:
                identity = _identity_description(user)
                if identity.id not in unique_users:
                    unique_users.add(identity.id)
                    users[self.IDENTITY].append(identity)

                access_description = _access_description(user)
                if access_description is not None:
                    users[self.ACCESS].append(access_description)

            if currentPage < totalPages:
                currentPage += 1
            else:
                break

            response = self.conn.client.request("searchMoreWithId",
                                                searchId=searchId,
                                                pageIndex=currentPage)
            results = response.body.searchResult
            status = results.status
            success = status.isSuccess

            if not success:
                raise Exception("NetSuite searchMoreWithId failed with {status['statusDetail'][0]}")

        return users

def _identity_description(user) -> IdentityDescription:
    name = user.basic.entityId[0].searchValue
    email = user.basic.email[0].searchValue
    internal_id = user.basic.internalId[0].searchValue.internalId

    return IdentityDescription(
        id=internal_id,
        name=name,
        type=IdentityTypes.User.value,
        email=email,
        status=_user_status(user),
    )


def _access_description(user) -> AccessDescription:
    internal_id = user.basic.internalId[0].searchValue.internalId
    role_id = user.basic.role[0].searchValue.internalId

    ad = None
    if _NETSUITE_ROLE_MAP.get(role_id) is not None:
        ad =  AccessDescription(
                fromIdentityId=internal_id,
                toAssetId=_ASSET_ID,
                accessType=_NETSUITE_ROLE_MAP[role_id]["type"],
                accessName=_NETSUITE_ROLE_MAP[role_id]["name"],
            )
    else:
        log.error("Missing NetSuite role id",
                    extra={"role_id": role_id})

    return ad

def _user_status(user: dict) -> UserStatus:
    if user.basic.isInactive[0].searchValue:
        return UserStatus.Disabled
    return UserStatus.Enabled
