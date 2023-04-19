"""Authomize connector for GitLab"""

from urllib.parse import urlparse
import datetime as dt
from logger import logger as log
import os
import re
from typing import Union, Tuple

from authomize.rest_api_client import (
    AccessDescription,
    AccessTypes,
    AssetDescription,
    AssetsInheritance,
    AssetTypes,
    IdentityDescription,
    IdentitiesInheritance,
    IdentityTypes,
    UserStatus,
)

from autohelp.gitlab import GitLabAdminHelper, GitLabGraphQLAdminHelper

from gitlab.v4.objects.groups import Group
from gitlab.v4.objects.projects import Project
from gitlab.v4.objects.users import User
from gitlab.v4.objects import GroupMember
from gitlab.v4.objects import ProjectMember

from connectors import Base

CONNECTOR_ID = "SecAuto GitLab"

_ROLE_NAMES = {
    10: "guest",
    20: "reporter",
    30: "developer",
    40: "maintainer",
    50: "owner",
}
_ROLE_TYPES = {
    10: AccessTypes.List,
    20: AccessTypes.Read,
    30: AccessTypes.Write,
    40: AccessTypes.Administrative,
    50: AccessTypes.Owner,
}

_DEFAULT_GITLAB_INSTANCE = urlparse('https://gitlab.com')

_URLS = [
    "https://gitlab.com",
    "https://gitlab.com/gitlab-org",
    "https://gitlab.com/gitlab-org/gitaly",
    "https://gitlab.com/gitlab-org/release-tools",
    "https://gitlab.com/gitlab-com",
    "https://gitlab.com/gitlab-com/gl-infra/k8s-workloads/gitlab-helmfiles",
    "https://gitlab.com/gitlab-com/gl-infra/k8s-workloads/gitlab-com",
    "https://gitlab.com/gitlab-com/sales-team/field-operations/salesforce-src",
    "https://gitlab.com/gitlab-cookbooks",
    "https://ops.gitlab.net",
    "https://ops.gitlab.net/gitlab-org/release",
    "https://ops.gitlab.net/gitlab-com/engineering/patcher",
    "https://ops.gitlab.net/gitlab-com/gl-infra",
    "https://ops.gitlab.net/gitlab-com/gl-infra/chef-repo",
    "https://ops.gitlab.net/gitlab-com/gl-infra/config-mgmt",
    "https://ops.gitlab.net/gitlab-com/gl-infra/deploy-tooling",
    "https://ops.gitlab.net/gitlab-com/gl-infra/k8s-workloads/gitlab-com",
    "https://ops.gitlab.net/it-infra-realm",
]


class Connector(Base):
    """
    Authomize connector for GitLab instances, groups and projects
    """

    def __init__(self) -> None:
        super().__init__(CONNECTOR_ID)

    # due to the complexity and diversity of the handled data sources this
    # connector relies on a multipurpose class dictionary attribute to store
    # data and objects as they are processed and calculated for later usage

    CACHE = {
        'users': {},  # user information web_url -> name, GitLab email
        'groups': [],  # list of groups processed sofar
        'projects': [],  # list of projects processed sofar
        'identities': {},  # IdentityDescriptions to be collected
        'inherited_identities': {},  # IdentitiesInheritances to be collected
        'assets': {},  # AssetDescriptions to be collected
        'inherited_assets': {},  # AssetsInheritances to be collected
        'accesses': {},  # AccessDescriptions to be collected
        'RESTclients': {},  # instance -> REST python-gitlab client
        'GraphQLclients': {},  # instance -> GraphQL client
    }

    def collect(self) -> dict:
        """Implement Base.collect()"""

        result = {}

        result[Base.ASSET] = []
        result[Base.IDENTITY] = []
        result[Base.ACCESS] = []
        result[Base.INHERITANCE_IDENTITY] = []
        result[Base.INHERITANCE_ASSET] = []

        for url in _URLS:
            self.process_url(url)

        new_assets = self.CACHE['assets'].values()
        result[Base.ASSET].extend(new_assets)
        new_identities = self.CACHE['identities'].values()
        result[Base.IDENTITY].extend(new_identities)
        new_accesses = self.CACHE['accesses'].values()
        result[Base.ACCESS].extend(new_accesses)
        new_inherited_ids = self.CACHE['inherited_identities'].values()
        result[Base.INHERITANCE_IDENTITY].extend(new_inherited_ids)
        new_inherited_asstes = self.CACHE['inherited_assets'].values()
        result[Base.INHERITANCE_ASSET].extend(new_inherited_asstes)

        return result

    def process_url(self, href: str):
        """
        Prepares the client(s) and context required to process a URL
        and decides whether it should be processed as a GitLab instance
        or a GitLab resource (group or project)

        Args:
            href (str): URL of a GitLab resource
        """

        log.debug(
            'Processing Url',
            extra={
                'href': href,
            },
        )

        url = urlparse(href)
        instance = url.hostname

        if href not in self.CACHE['RESTclients']:
            rest_client = GitLabAdminHelper(instance)

            # instead of preparing a GraphQL client per instance, we rely on gitlab.com for
            # resolving identities, an alternative would be using each resource's instance
            # to retrive user information, but GitLab.com is a better source

            gql_client = GitLabGraphQLAdminHelper(_DEFAULT_GITLAB_INSTANCE.hostname)

            self.CACHE['RESTclients'][instance] = rest_client
            self.CACHE['GraphQLclients'][instance] = gql_client
            self.CACHE['users'][instance] = {}
        else:
            rest_client = self.CACHE['RESTclients'][url.hostname]
            gql_client = self.CACHE['GraphQLclients'][url.hostname]

        if len(url.path) == 0:
            # href is an instance
            self.process_instance(url)
        else:
            resource_url, members_map = rest_client.get_members_map(href)

            # the routines required to parse the members map
            # fully is included but shall not be used until
            # Authomize solves their stability problems.
            # it is however included for future reference.
            #
            # self.parse_members_map(client, rurl, rmembers)

            member_list = rest_client._flatten_members_map(members_map, False)

            if isinstance(members_map['object'], Project):
                self.CACHE['projects'].append(resource_url)
            elif isinstance(members_map['object'], Group):
                self.CACHE['groups'].append(resource_url)

            self.process_members_list(href, member_list)

    def process_instance(self, url: str):
        """
        For a given GitLab instance, retrieve the administrative users, do a best-effort
        attempt at gathering their information from GitLab.com and create corresponding access
        descriptions

        Args:
            url (str): URL to the GitLab instance in question
        """

        href = url.geturl()
        instance = self.get_url_instance(href)
        rest_client = self.CACHE['RESTclients'][instance]
        gql_client = self.CACHE['GraphQLclients'][instance]

        assets = self.CACHE['assets']
        accesses = self.CACHE['accesses']
        new_asset = None

        if href not in assets:
            new_asset = AssetDescription(
                id=url.hostname,
                name=url.hostname,
                type=AssetTypes.Application,
                href=href,
            )

            assets[href] = new_asset
        else:
            new_asset = assets[href]

        # First, attempt clean-up of admin suffix and prefixes in administrator usernames
        # Then, retrieve their web_url, name and GitLab email to populates the user CACHE
        # with the data coming via the GraphQL client

        admins = list(rest_client.get_users(admins=True))
        cusernames = [gql_client.get_cannonical_username(m.username) for m in admins]
        cusers = gql_client.get_users_info(cusernames)
        self.CACHE['users'].update(cusers)

        for u in admins:
            locator = f'{href}-{u.username}@admin'
            member_id = self.prepare_user(u)

            new_access = AccessDescription(
                fromIdentityId=member_id.id,
                toAssetId=new_asset.id,
                accessType=AccessTypes.Owner,
                accessName="Instance Administrator",
            )

            accesses[locator] = new_access

            log.debug(
                'Preparing Instance Administrative Access',
                extra={
                    'locator': locator,
                    'resource': href,
                    'access': new_access.accessName,
                    'identity': None if member_id is None else member_id.id,
                },
            )

    def process_members_list(self, href: str, members: list):
        """
        First, populates the user CACHE with the user data coming via
        the GraphQL client. Second, triggers the creation of
        Assets, Identities and AccessDescriptions for a flattened
        membership map.

        Args:
            href (str): URL of a GitLab resource
            members (list): a flattened membership map for the respective
            GitLab resource
        """

        instance = self.get_url_instance(href)
        gql_client = self.CACHE['GraphQLclients'][instance]

        rmembers, _ = zip(*members)

        usernames = [m.username for m in rmembers]
        users = gql_client.get_users_info(usernames)
        self.CACHE['users'].update(users)

        for member, source_path in members:
            self.prepare_resource_membership(member, href, source_path)

    def prepare_resource_membership(
        self,
        member: Union[ProjectMember, GroupMember, User],
        href: str,
        source_path: list,
    ) -> Tuple[IdentitiesInheritance, AccessDescription]:
        """
        Creates an AccessDescription and if necessary an IdentityInheritance for a given resource and a user

        Args:
            member (Union[ProjectMember, GroupMember, User]): member which receives access to the resource
            href (str): URL of the resource
            source_path (list): a source_path as calculated by _flatten_members_map

        Returns:
            Tuple[IdentitiesInheritance, AccessDescription]
        """

        inherited_ids = self.CACHE['inherited_identities']
        accesses = self.CACHE['accesses']
        groups = self.CACHE['groups']

        member_id = None
        new_inherited_id = None
        new_access = None
        locator = f'{href}-{member.username}@{member.access_level}'
        source_path = f'{ _ROLE_NAMES[member.access_level]} VIA {">".join(source_path)}'

        if locator not in inherited_ids:
            member_id = self.prepare_user(member)
            resource_id, rasset = self.prepare_resource(href)

            new_access = AccessDescription(
                fromIdentityId=member_id.id,
                toAssetId=rasset.id,
                accessType=_ROLE_TYPES[member.access_level],
                accessName=source_path,
            )

            accesses[locator] = new_access

            if href in groups:
                new_inherited_id = IdentitiesInheritance(
                    fromId=member_id.id,
                    toId=resource_id.id,
                )
                inherited_ids[locator] = new_inherited_id

        else:
            if href in groups:
                new_inherited_id = inherited_ids[locator]
            new_access = accesses[locator]

        log.debug(
            'Preparing Resource Membership',
            extra={
                'locator': locator,
                'resource': href,
                'access': new_access.accessName,
                'identity': None if member_id is None else member_id.id,
                'is_group': False if new_inherited_id is None else True,
                'source_path': source_path,
            },
        )

        return new_inherited_id, new_access

    def prepare_user(
        self, member: Union[User, ProjectMember, GroupMember]
    ) -> IdentityDescription:
        """
        Creates an IdentityDescription for a GitLab User, GroupMember,
        or ProjectMember

        Args:
            member (User, ProjectMember, GroupMember): GitLab user or member

        Returns:
            IdentityDescription: an IdentityDescription for the input member
        """

        identities = self.CACHE['identities']
        new_id = None
        locator = member.web_url
        instance = self.get_url_instance(locator)
        gql_client = self.CACHE['GraphQLclients'][instance]

        if locator not in identities:
            name = None
            email = None

            # check whether a matching identity for a GitLab
            # team member could be found in the users cache
            # and if so use that name and email.
            cgitlab_user = self.CACHE['users'].get(
                gql_client.get_cannonical_weburl(member.username)
            )

            # collect the shortest @gitlab.com email as some
            # employees have many aliases and +-addresses they
            # use for different purposes
            if cgitlab_user:
                name, emails = cgitlab_user
                emails = sorted(emails, key=len)
                for e in emails:
                    email = e
                    if re.match('^.*gitlab.com', e):
                        break

            if name is None:
                name = member.username
            if email is None:
                email = 'uknown@gitlab.com'

            new_id = IdentityDescription(
                id=locator,
                name=name,
                status=UserStatus.Enabled
                if member.state == 'active'
                else UserStatus.Disabled,
                type=IdentityTypes.User,
                href=locator,
                email=email,
                createdAt=dt.datetime.strptime(
                    member.created_at, '%Y-%m-%dT%H:%M:%S.%fZ'
                ),
            )
            identities[locator] = new_id
        else:
            new_id = identities[locator]
        return new_id

    def prepare_resource(self, href: str) -> Tuple[IdentitiesInheritance, AssetDescription]:
        """
        Creates the AssetDescription (for projects) and if necessary (for groups) IdentitiesInheritance
        for a resource

        Args:
            href (str): GitLab resource URL

        Returns:
            Tuple[IdentitiesInheritance, AccessDescription]: inherited identity and asset for the corresponding
            GitLab resource
        """

        new_id = None
        new_asset = None

        if href in self.CACHE['projects']:
            new_asset = self.prepare_project(href)
        else:
            new_id, new_asset = self.prepare_group(href)

        return new_id, new_asset

    def prepare_group(self, href: str) -> Tuple[IdentitiesInheritance, AssetDescription]:
        """
        Handles the creation of an AssetDescription for a GitLab group

        Args:
            href (str): web_url of the group

        Returns:
            Tuple[IdentitiesInheritance,AssetDescription]: corresponding IdentitiesInheritance and AssetDescription
        """

        identities = self.CACHE['identities']
        assets = self.CACHE['assets']
        new_id = None
        new_asset = None

        if href not in identities:
            new_id = IdentityDescription(
                id=href,
                name=href.replace('https://', ''),
                href=href,
                type=IdentityTypes.Group,
            )

            identities[href] = new_id

            # assets are enough for implementing inheritance of resources
            # but are insufficient when a resource has been shared with
            # a group outside its hierarchy. Therefore, we need IdentitiesInheritances

            # the IdentityDescription wil be used to create AccessDescriptions
            # when resources are shared with this group

            new_asset = AssetDescription(
                id=href,
                name=href.replace('https://', ''),
                type=AssetTypes.Folder,
                href=href,
            )

            assets[href] = new_asset
        else:
            new_id = identities[href]
            new_asset = assets[href]
        return new_id, new_asset

    def prepare_project(self, href: str) -> AssetDescription:
        """
        Handles the creation of an AssetDescription for a GitLab project

        Args:
            href (str): web_url of the project

        Returns:
            Tuple[AssetDescription]:
        """

        assets = self.CACHE['assets']
        new_asset = None

        if href not in assets:
            new_asset = AssetDescription(
                id=href,
                name=href.replace('https://', ''),
                type=AssetTypes.GitRepository,
                href=href,
            )

            assets[href] = new_asset
        else:
            new_asset = assets[href]
        return new_asset

    def get_url_instance(self, href: str) -> str:
        """
        For a given resource URL parse it and return the corresponding instance
        or hostname part of said URL

        Args:
            href (str): resource URL

        Returns:
            str: instance (hostname) of the input URL
        """
        return urlparse(href).hostname

    # the methods below are provided for reference, as they are not used currently
    # they are not used as mirroring the full hierarchy of GitLab resources in
    # Authomize results in very confusing workflows for campaigns and while navigating
    # through access policies

    def process_members_map(
        self,
        client: GitLabAdminHelper,
        resource_url: str,
        members_map: dict,
        source_url: str = None,
        override_access: int = None,
    ):
        """
        Process a members map as returned by gather_members_map in GitLabAdminHelper
        mirroing the full hierarchy of groups, projects and members in Authomize

        Args:
            client (GitLabAdminHelper): the
            resource_url (str): URL of the resource
            members_map (dict): members map to be processed
            source_url (str, optional): URL of the resource previously processed,
            used internally to keep state in recursive calls. Defaults to None.
            override_access (int, optional): If a share relationship is being processed,
            override access levels to the members of the group receiving the share.
            Defaults to None.

        Returns:
            _type_: _description_
        """

        share_recipient = 'shared_with_access' in members_map
        if share_recipient:
            override_access = members_map['shared_with_access']

        _, _ = self.prepare_resource(resource_url)

        if source_url is not None:
            self.CACHE['groups'].append(resource_url)

            if share_recipient:
                self.prepare_share(source_url, resource_url, override_access)
            else:
                # only create inheritance if the resource and the breadcrumb are neighbors
                if source_url.replace(resource_url, '').count('/') == 1:
                    self.prepare_inheritance(resource_url, source_url)

        for k, v in members_map.items():
            if k == 'direct':
                for member in v:
                    if (
                        override_access is not None
                        and override_access < member.access_level
                    ):
                        member.access_level = override_access
                    self.prepare_resource_membership(client, member, resource_url)

            elif isinstance(v, dict):
                self.process_members_map(client, k, v, resource_url, override_access)

        return True

    def prepare_inheritance(
        self, parent: str, child: str
    ) -> Tuple[IdentitiesInheritance, AssetsInheritance]:
        """
        Creates and stores an IdentityInheritance and AssetInheritance for two given
        parent and child GitLab resources (be it group and group or group and project)

        Args:
            parent (str): URL to GitLab parent resource
            child (str): URL to GitLab child resource

        Returns:
            Tuple[IdentitiesInheritance, AssetsInheritance]: corresponding Identity and Asset inheritances
        """

        inherited_ids = self.CACHE['inherited_identities']
        inherited_assets = self.CACHE['inherited_assets']
        new_inherited_id = None
        new_inherited_asset = None
        locator = f'{parent}-{child}'

        if locator not in inherited_ids:
            parent_id, parent_asset = self.prepare_resource(parent)
            child_id, child_asset = self.prepare_resource(child)

            # Authomize's API has a mistake, from and to are flipped
            # for IdentitiesInheritance
            new_inherited_asset = AssetsInheritance(
                fromId=parent_asset.id,
                toId=child_asset.id,
            )

            inherited_assets[locator] = new_inherited_asset

            if parent in self.CACHE['groups'] and child in self.CACHE['groups']:
                new_inherited_id = IdentitiesInheritance(
                    fromId=child_id.id,
                    toId=parent_id.id,
                )
                inherited_ids[locator] = new_inherited_id

        else:
            if parent in self.CACHE['groups'] and child in self.CACHE['groups']:
                new_inherited_id = inherited_ids[locator]
            new_inherited_asset = inherited_assets[locator]

        log.debug(
            'Preparing Resource Inheritance',
            extra={
                'locator': locator,
                'parent': parent,
                'passet': parent_asset.id,
                'child': child,
                'casset': child_asset.id,
                'identity': None if new_inherited_id is None else new_inherited_id.id,
            },
        )

        return new_inherited_id, new_inherited_asset

    def prepare_share(
        self, resource: str, group: str, access_level: int
    ) -> AccessDescription:
        """
        Creates and stores an AccessDescription for a given GitLab resource (group or project)
        and the group it has been shared with

        Args:
            resource (str): URL to GitLab resource which has been shared
            group (str): URL to GitLab group with which the resource was shared
            access_level (int): GitLab level of access with which said resource was shared

        Returns:
            AccessDescription: the corresponding AccessDescription for the relationship
        """
        accesses = self.CACHE['accesses']
        new_access = None
        locator = f'{resource}-{group}@{access_level}'

        if locator not in accesses:
            _, resource_asset = self.prepare_resource(resource)
            group_id, _ = self.prepare_group(group)

            new_access = AccessDescription(
                fromIdentityId=group_id.id,
                toAssetId=resource_asset.id,
                accessType=_ROLE_TYPES[access_level],
                accessName=_ROLE_NAMES[access_level],
            )

            accesses[locator] = new_access

        else:
            new_access = accesses[locator]

        log.debug(
            'Preparing Share',
            extra={
                'locator': locator,
                'resource': resource,
                'asset': resource_asset.id,
                'group': group,
                'group': group_id.id,
                'access_level': access_level,
            },
        )
        return new_access
