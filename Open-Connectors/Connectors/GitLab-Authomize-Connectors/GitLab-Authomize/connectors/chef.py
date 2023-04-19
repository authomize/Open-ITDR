"""Authomize connector for Chef"""
import os
import hashlib
from urllib.parse import urlparse
from datetime import datetime, timezone
import base64

from requests import Request, Session

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from authomize.rest_api_client import (
    AccessDescription,
    AccessTypes,
    AssetDescription,
    AssetTypes,
    IdentityDescription,
    IdentitiesInheritance,
    IdentityTypes,
)

from connectors import Base

# Name of connector as seen in the Authomize UI
CONNECTOR_ID = "Chef"

_ASSETS = [
    {
        # bundle exec knife search node 'fqdn:customers*gitlab-subscriptions-prod.internal
        "name": "CustomersDOT",
        "id": 5,
        "fqdn": "customers*gitlab-subscriptions-prod.internal",
        "href": "https://customers.gitlab.com",
    },
    {
        # bundle exec knife search node 'fqdn:*gitlab-db-benchmarking.internal'
        "name": "DBBenchmarking",
        "id": 6,
        "fqdn": "*gitlab-db-benchmarking.internal",
        "href": None,
    },
    {
        # bundle exec knife search node 'fqdn:bastion*gitlab-production.internal'
        "name": "Bastion",
        "id": 7,
        "fqdn": "bastion*gitlab-production.internal",
        "href": None,
    },
    {
        # bundle exec knife search node 'fqdn:chef*gitlab-ops.internal'
        "name": "Chef",
        "id": 8,
        "fqdn": "chef*gitlab-ops.internal",
        "href": "https://chef.gitlab.com",
    },
    {
        # bundle exec knife search node 'fqdn:console*gitlab-production.internal'
        "name": "Console",
        "id": 9,
        "fqdn": "console*gitlab-production.internal",
        "href": None,
    },
]

_CHEF_BASEURL = "https://chef.gitlab.com"
_CHEF_METHOD = "GET"
_CHEF_PORT = "443"


# required headers as per https://docs.chef.io/server/api_chef_server/#required-headers
DEFAULT_HEADERS = {
    "Accept": "application/json",
    # not needed as we only rely on GET but here for readability purposes
    # https://docs.chef.io/server/api_chef_server/#requirements
    "Content-Type": "application/json",
    "User-Agent": "security-automation-authomize",
    "X-Chef-Version": "14.15.6",
    "X-Ops-Server-API-Version": "1",
    "X-Ops-Sign": "version=1.3",
    "X-Ops-UserId": "security-automation",
    "Host": "PENDING",
    "Method": "PENDING",
    "Path": "PENDING",
    # i.e: /organizations/gitlab/_status
    "X-Ops-Timestamp": "PENDING",
    "X-Ops-Content-Hash": "PENDING",
    "X-Ops-Authorization-N": "PENDING",
}


def timestamp_now_RFC3339():
    # timestamp in required RFC3339 format
    # as per https://docs.chef.io/server/api_chef_server/#canonical-header-format-13-using-sha-256

    timestampRFC3339 = datetime.now(timezone.utc)
    timestampRFC3339 = timestampRFC3339.replace(microsecond=0)
    timestampRFC3339 = timestampRFC3339.isoformat()
    timestampRFC3339 = timestampRFC3339.replace("+00:00", "Z")

    return timestampRFC3339


def _chef_query_sign(request: Request, privateKey):
    # Canonical Header Format 1.3 using SHA-256 structure according to
    # https://docs.chef.io/server/api_chef_server/#canonical-header-format-13-using-sha-256

    canonicalHeader = f"""Method:{request.headers["Method"]}
Path:{request.headers["Path"]}
X-Ops-Content-Hash:{request.headers["X-Ops-Content-Hash"]}
X-Ops-Sign:{request.headers["X-Ops-Sign"]}
X-Ops-Timestamp:{request.headers["X-Ops-Timestamp"]}
X-Ops-UserId:{request.headers["X-Ops-UserId"]}
X-Ops-Server-API-Version:{request.headers["X-Ops-Server-API-Version"]}"""

    canonicalHeader = canonicalHeader.encode()

    key = serialization.load_pem_private_key(
        base64.b64decode(os.environ["CHEF_KEY"]), password=None
    )

    signature = key.sign(canonicalHeader, padding.PKCS1v15(), hashes.SHA256())

    encoded = base64.b64encode(signature)

    n = len(encoded)
    for i in range(n // 60 + 1):
        lBound = i * 60
        uBound = (i + 1) * 60
        if uBound > n:
            uBound = n

        request.headers["X-Ops-Authorization-" + str(i + 1)] = encoded.decode()[
            lBound:uBound
        ]

    return request


def _chef_query_send(endpoint: str, query: str = None):

    req = Request(
        _CHEF_METHOD, f"{_CHEF_BASEURL}/{endpoint}", params={"q": query})
    req = req.prepare()
    requestBody = req.body if req.body is not None else ""

    bodyHash = hashlib.sha256()
    bodyHash.update(requestBody.encode())
    bodyHash = bodyHash.digest()
    hashedContent = base64.b64encode(bodyHash)
    hashedContent = hashedContent.decode("UTF-8")

    finalHeaders = DEFAULT_HEADERS

    finalHeaders.update({"X-Ops-Content-Hash": hashedContent})
    url = urlparse(req.url)
    finalHeaders.update({"Host": url.netloc + ":" + _CHEF_PORT})
    finalHeaders.update({"Path": url.path})
    finalHeaders.update({"Method": req.method})
    finalHeaders.update({"X-Ops-Timestamp": timestamp_now_RFC3339()})

    req.headers = finalHeaders

    req = _chef_query_sign(req, None)

    s = Session()
    resp = s.send(req)

    resp.raise_for_status()
    data = resp.json()
    return data


class Connector(Base):
    """
    Authomize connector for Chef
    """

    def __init__(self) -> None:
        super().__init__(CONNECTOR_ID)

    def collect(self) -> dict:
        """Implement Base.collect()"""

        result = {}

        result[Base.ASSET] = []
        result[Base.IDENTITY] = []
        result[Base.ACCESS] = []
        result[Base.INHERITANCE_IDENTITY] = []
        result[Base.INHERITANCE_ASSET] = []

        uniqueidents = set()
        uniquegroups = set()

        # for the purposes of this connector, an asset is an environment
        # composed, often, of multiple nodes
        for asset in _ASSETS:

            # we create and add asset description for each environment
            assetDescription = AssetDescription(
                id=asset["id"],
                name=asset["name"],
                type=AssetTypes.Application,
                href=asset["href"],
            )

            result[Base.ASSET].append(assetDescription)

            # grab the nodes whose FQDN matches the wildcard expression for each environment
            nodes =_chef_nodes(asset["fqdn"])["rows"]
            
            for node in nodes:

                fqdn = node['automatic']['fqdn']
                nodeAssetDescription = AssetDescription(
                id=fqdn,
                name=fqdn,
                type=AssetTypes.Instance,
                href=asset["href"],
                )

                assetInheritance = IdentitiesInheritance(
                                    toId=nodeAssetDescription.id,
                                    fromId=assetDescription.id
                                )
                result[Base.ASSET].append(nodeAssetDescription)
                result[Base.INHERITANCE_ASSET].append(assetInheritance)

                # for each node in our target _ASSETS(environments), we create a UNIQUE AssetDescription
                node = _chef_node(fqdn)

                # for each of our desired _ASSETS, we attempt to access the node's
                # attribute default.gitlab_users.groups which describes the linux-level
                # groups a node gets provisioned to it by chef using
                # https://gitlab.com/gitlab-cookbooks/gitlab_users/-/blob/master/attributes/default.rb
                groups = node.get("default", {}).get(
                    "gitlab_users", {}).get("groups", [])

                # we now retrieve the members of each group and their
                # respective databags via the chef API
                databags_in_groups = _chef_databags_in_groups(groups)

                for g in groups:

                    # for each of the groups found in each desired _ASSETS, we create
                    # a UNIQUE IdentityDescription for that group from which other
                    # IdentityDescriptions of IdentityTypes.User will later inherit
                    if g not in uniquegroups:
                        gidentity = IdentityDescription(
                            id=g,
                            name=g,
                            type=IdentityTypes.Group,
                        )
                        uniquegroups.update([g])
                        result[Base.IDENTITY].append(gidentity)

                    # for each _ASSETS and for each of its groups we
                    #  determine the level of access that group has based on the node's definition
                    # https://gitlab.com/gitlab-com/gl-infra/chef-repo/-/blob/master/roles/prdsub-base.json#L15
                    node_sudoers = (
                        node.get("default", {})
                        .get("authorization", {})
                        .get("sudo", {})
                        .get("groups", [])
                    )

                    group_access_type = (
                        AccessTypes.Execute
                        if g not in node_sudoers
                        else AccessTypes.Administrative
                    )

                    # we create an access for the IdentityTypes.Group g with
                    # access type group_access_type
                    result[Base.ACCESS].append(
                        AccessDescription(
                            fromIdentityId=g,
                            toAssetId=nodeAssetDescription.id,
                            accessType=group_access_type,
                            accessName=g,
                        )
                    )

                for group, databags in databags_in_groups.items():
                    for db in databags:
                        # for each databag in each group provisioned to each _ASSET
                        # we create an IdentityInheritance that adds that user's
                        # databag as a member to the group, thus inheriting its accesses
                        
                        # user identities only need to be created once
                        identity = _chef_databag_identity(db)
                        if not identity.id in uniqueidents:
                            result[Base.IDENTITY].append(identity)
                            uniqueidents.update([db["name"]])

                        # while inheritances for a given user need to be
                        # created every time said user comes up in a given group
                        groupInheritance = IdentitiesInheritance(
                            fromId=identity.id, toId=group)
                        result[Base.INHERITANCE_IDENTITY].append(groupInheritance)

        return result


def _chef_nodes(fqdn: str) -> list:
    """retrieves and returns the Chef JSON objects found for a given FQDN or valid Chef search expression"""
    res = _chef_query_send(f"organizations/gitlab/search/node", f"fqdn:{fqdn}")
    return res


def _chef_node(fqdn: str) -> list:
    """retrieves and returns the Chef JSON object for a node given its FQDN"""
    res = _chef_query_send(f"organizations/gitlab/nodes/{fqdn}")
    return res


def _chef_databags_in_groups(groups: list) -> dict:
    """retrieves the user databags for a list of users and returns a dictionary mapping"""
    result = {}
    for g in groups:
        databags = _chef_query_send(
            "organizations/gitlab/search/users", f"groups:{g}")
        databags = databags["rows"]
        databags = [e for e in databags if e["raw_data"]["action"] == "create"]
        result[g] = databags

    return result


def _chef_databag_identity(databag: dict) -> dict:
    """creates an Authomize IdentityDescription out of a Chef databag"""

    raw = databag["raw_data"]

    id = databag["name"]
    email = raw.get("email", "").strip()
    username = raw.get("id", "").strip()
    name = raw.get("comment", databag["name"]).strip()

    identity = IdentityDescription(
        id=id,
        name=name,
        type=IdentityTypes.User,
        email=email,
        userName=username,
    )
    return identity
