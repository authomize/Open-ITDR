#!/usr/bin/env python3

import click

from logger import logger as log

from connectors import (
    Base,
    ava_tax,
    chef,
    coupa,
    gitlab,
    jamf,
    net_suite,
    tenable,
    test as test_connector,
    workday,
    workiva,
    xactly_incent,
    zuora,
)


####################
# CLI Entrypoint
####################


@click.group()
@click.option("--log-level", default="info", help="log level", show_default=True)
def cli(log_level="info"):
    """Authomize CLI"""
    log.set_level(log_level)


####################
# Connector Group
####################


@cli.group()
def connector():
    """Interact with configured Authomize connectors."""


@connector.command(name="list")
def list_connectors():
    """List Authomize connectors."""
    base = Base("base")
    connectors = base.list_connectors()
    for con in sorted(connectors, key=lambda x: x.serviceId.lower()):
        print(con.serviceId + ": " + con.id)


@connector.command()
@click.argument("connector_name")
def export(connector_name):
    """Export Authomize connector data."""
    found = False
    connectors = []
    for con in Base.__subclasses__():
        con = con()
        connectors.append(con.connector_name)
        if connector_name.lower() == con.connector_name.lower():
            connector_name = con
            found = True
            break

    if not found:
        con_str = ""
        for con in sorted(connectors, key=str.casefold):
            con_str += f"  - {con}\n"
        raise click.ClickException(
            f"{connector_name } connector not found. Must be one of: \n{con_str}"
        )

    base = Base(connector_name)
    base.export_connector()


####################
# Sync Group
####################


@cli.group()
@click.option(
    "--test",
    help="Print data from connector without syncing to Authomize.",
    is_flag=True,
)
def sync(test=False):
    """Run data syncs from third party applications into Authomize."""
    Base.test = test


@sync.command(name="all")
def all_connectors():
    """Iterate through all configured connectors and sync to Authomize."""
    for con in Base.__subclasses__():
        if hasattr(con, "test_connector"):
            log.debug("skipping test connector", extra={"connector": con.__name__})
            continue
        con().run()


@sync.command(name="ava-tax")
def sync_ava_tax():
    """Sync data from AvaTax to Authomize."""
    ava_tax.Connector().run()


@sync.command(name="chef")
def sync_chef():
    """Sync data from chef.gitlab.com to Authomize."""
    chef.Connector().run()


@sync.command(name="coupa")
def sync_coupa():
    """Sync data from Coupa to Authomize."""
    coupa.Connector().run()


@sync.command(name="gitlab")
def sync_gitlab():
    """Sync data from GitLab instances and resources to Authomize."""
    gitlab.Connector().run()


@sync.command(name="jamf")
def sync_jamf():
    """Sync data from Jamf to Authomize."""
    jamf.Connector().run()


@sync.command(name="net-suite")
def sync_net_suite():
    """Sync data from NetSuite to Authomize."""
    net_suite.Connector().run()


@sync.command(name="tenable")
def sync_tenable():
    """Sync data from AvaTax to Authomize."""
    tenable.Connector().run()


@sync.command(name="workday")
def sync_workday():
    """Sync data from Workday to Authomize."""
    workday.Connector().run()


@sync.command(name="workiva")
def sync_workiva():
    """Sync data from Workiva to Authomize."""
    workiva.Connector().run()


@sync.command(name="xactly-incent")
def sync_xactly_incent():
    """Sync data from Xactly Incent to Authomize."""
    xactly_incent.Connector().run()


@sync.command(name="zuora")
def sync_zuora():
    """Sync data from zuora to Authomize."""
    zuora.Connector().run()


####################
# Test Group
####################


@cli.group(name="test")
def test_group():
    """Test various application functionality."""


@test_group.command()
def log_error() -> None:
    """Log a test message at ERROR level."""
    log.error("Test message at ERROR level.")


@test_group.command()
def log_fatal() -> None:
    """Log a test message at FATAL level."""
    log.fatal("Test message at FATAL level.")


@test_group.command(name="connector")
def test_conn() -> None:
    """Write test connector data to Authomize."""
    test_connector.FakeConnector().run()


if __name__ == "__main__":
    cli()
