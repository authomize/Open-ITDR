"""Base module for Authomize connectors"""

import functools
import json
import os
import time
import urllib.request
from datetime import datetime
from enum import Enum
from itertools import chain, islice
from typing import Any, Iterator, List

from authomize.rest_api_client import Client, ItemsBundleSchema
from authomize.rest_api_client.generated.schemas import (
    ConnectorStatus,
    RestApiConnectorSchema,
    TransactionStateType,
)
from requests.exceptions import HTTPError

from logger import logger as log

# Max allowed size of every POST /items request - 1MB.
# Max allowed count of entity items in POST /items request - 10,000.
# Max allowed count of entity items in a transaction - 1,000,000.
# https://gitlab.com/gitlab-com/gl-security/security-assurance/continuous-control-monitoring/uploads/db5f9195054fafc67e953cdc08fb76d6/CSM-ConnectorsRestAPIguide-281221-0853.pdf

# Max number of items to send when extending a transaction
# This should be enough to not exceed the thresholds but should be tested with real data
_CHUNK_SIZE: int = 250

# Amount of seconds to wait for each step of a transaction to be applied
_TRANSACTION_TIMEOUT: int = 1800

# Amount of seconds to wait to see if transaction has been updated
_APPLY_BACKOFF: int = 15

# Number of times to retry a remote operation
_RETRY_LIMIT = 3
# Number of seconds to wait between retries
_RETRY_DELAY = 20


class SyncResult(Enum):
    """Result status for the Connector run() method."""

    SUCCESS = 0
    SERVICE_FAILURE = 1
    AUTHOMIZE_FAILURE = 2
    OTHER_FAILURE = 3


class SyncFailure(Exception):
    """Raised for errors in the Connector run() method."""

    def __init__(self, result):
        super().__init__()
        self.result = result


def retry_request():
    """The default retry function for an HTTPError response."""
    return retry_on_error(SyncResult.SERVICE_FAILURE)

def retry_on_server_error(failure, limit=_RETRY_LIMIT, delay=_RETRY_DELAY):
    """Retry the decorated function in case of 5xx responses."""
    return retry_on_error(failure, limit, delay, 500)

def retry_on_error(failure, limit=_RETRY_LIMIT, delay=_RETRY_DELAY, code=None):
    """Retry the decorated function in case of HTTPError responses.

    Args:
        failure (SyncResult): The failure type.
        limit (int, optional): The limit for retry attempts.
        delay (int, optional): The delay in seconds between retries.
        code (int, optional): Threshold response status code for retries. If status code is
            less than the supplied argument, retries are not attempted.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(limit):
                try:
                    return func(*args, **kwargs)
                except HTTPError as exp:
                    if exp.response is None or (code and exp.response.status_code < code):
                        raise
                    log.warning(
                        "Server error",
                        extra={
                            "status": exp.response.status_code,
                            "failure": failure,
                        },
                    )
                # i is zero indexed
                if i + 1 < limit:
                    log.debug(f"Retrying operation: {func.__name__}")
                    time.sleep(delay)

            raise SyncFailure(failure)

        return wrapper

    return decorator


class Base:
    """Base class for Authomize connectors.

    Args:
        connector_id (str): The ID of the connector.
    """

    ACCESS = "access"
    ASSET = "assets"
    IDENTITY = "identities"
    INHERITANCE_ASSET = "inheritanceAssets"
    INHERITANCE_IDENTITY = "inheritanceIdentities"
    SERVICE = "services"

    test = False  # Collect data, but do not talk to Authomize

    def __init__(self, connector_name: str) -> None:
        self.connector_name = connector_name
        self.connector_id = None
        self._trans = None
        self._client = Client(auth_token=os.environ["AUTHOMIZE_TOKEN"])

    def run(self) -> SyncResult:
        """Run the sync job with the connector"""
        log.info(
            "Starting sync job",
            extra={"event": "sync_started", "connector": self.connector_name},
        )
        try:
            data = self._collect_data()
            if Base.test is False:
                counts = self._upload_data(data)
            else:
                counts = self._print_data(data)
            log.info(
                "Finished sync job",
                extra={
                    "event": "sync_finished",
                    "connector": self.connector_name,
                    "items_uploaded": counts,
                },
            )
            return SyncResult.SUCCESS
        # Broad exception here since there is no control over the connector and
        # we want to ensure that any errors get logged.
        # pylint: disable=broad-except
        except Exception as exp:
            log.error(
                exp, extra={"event": "sync_failed", "connector": self.connector_name}
            )
            if isinstance(exp, SyncFailure):
                return exp.result
            return SyncResult.OTHER_FAILURE

    def collect(self) -> dict:
        """Collect data from a third party application.

        Returns:
            data (dict): A dictionary with keys of the Authomize data type
                mapped to iterators of the data elements.
        """
        raise NotImplementedError("Connector not implemented")

    @retry_on_server_error(SyncResult.SERVICE_FAILURE)
    def _collect_data(self) -> dict:
        return self.collect()

    @retry_on_server_error(SyncResult.AUTHOMIZE_FAILURE)
    def _upload_data(self, data) -> dict:
        counts = {}
        self.connector_id = self._get_connector_id()
        self._begin_transaction()
        for data_type, items in data.items():
            counts[data_type] = self._sync_items(data_type, items)
        self._apply_transaction()
        return counts

    def _print_data(self, data) -> dict:
        counts = {}
        for data_type, items in data.items():
            print(f"\n##### {data_type} #####\n")
            count = 0
            for item in items:
                print(item)
                count += 1
            counts[data_type] = count
        print("\n##### counts #####\n")
        for data_type, count in counts.items():
            print(f"{data_type}: {count}")
        return counts

    def _begin_transaction(self) -> None:
        """Initiate a transaction to load data into Authomize."""
        log.debug("starting transaction", extra={"connector": self.connector_name})
        self._trans = self._client.create_transaction(self.connector_id)

    def _apply_transaction(self) -> None:
        """Apply transaction to commit data into Authomize."""
        log.debug(
            "applying transaction",
            extra={
                'connector':self.connector_name,
                'connector_id':self.connector_id,
                'transaction':self._trans.id
                }
            )
        self._client.apply_transaction(self.connector_id, self._trans.id)
        start = datetime.now()
        state = None
        while True:
            trans = self._client.retrieve_transaction(self.connector_id, self._trans.id)
            if state != trans.state:
                state = trans.state
                log.debug(
                    "transaction state changed",
                    extra={
                        "connector": self.connector_name,
                        "transaction_state": trans.state,
                    },
                )
                start = datetime.now()
            if trans.state == TransactionStateType.Complete:
                break
            if trans.state == TransactionStateType.Failed:
                log.warning(
                    "transaction failed",
                    extra={
                        "validations": trans.validations,
                        "warnings": trans.warnings,
                    },
                )
                raise Exception("transaction failed")
            if (datetime.now() - start).seconds >= _TRANSACTION_TIMEOUT:
                log.warning(
                    "Transaction timed out", extra={"connector": self.connector_name}
                )
                break
            time.sleep(_APPLY_BACKOFF)
        self._trans = None

    def _extend_transaction(self, items: ItemsBundleSchema) -> None:
        self._client.extend_transaction_items(self.connector_id, self._trans.id, items)

    def _sync_items(self, kind: str, items: Iterator[Any]) -> int:
        count = 0
        for chunk in _chunk_items(items):
            count += len(chunk)
            kwargs = {kind: chunk}
            bundle = self._items_bundle(**kwargs)
            self._extend_transaction(bundle)
        return count

    def list_connectors(self) -> Iterator[RestApiConnectorSchema]:
        """Retrieve listing of all Authomize connectors.

        Returns:
            Iterator[RestApiConnectorSchema]
        """
        params = {"limit": 50, "skip": 0}
        while True:
            connectors = self._client.list_connectors(params=params)
            for connector in connectors.data:
                if connector.status != ConnectorStatus.deleted:
                    yield connector

            if connectors.pagination.total <= params["limit"] + params["skip"]:
                break
            params["skip"] += params["limit"]

    def export_connector(self) -> None:
        """Export Authomize connector data."""
        cid = self._get_connector_id()
        export = self._client.http_get(f"/v1/connectors/{cid}/export")[0]
        if not os.path.exists("exports"):
            os.makedirs("exports")
        date = datetime.today().strftime("%Y-%m-%d")
        outfile = f"exports/{self.connector_name}-{date}.zip"
        url = export["exportUrl"]
        # Checking to ensure that URL is an HTTP endpoint
        # Adding nosec since bandit still warns about the use of urlretrieve
        if url.lower().startswith("https:"):
            urllib.request.urlretrieve(url, outfile)  # nosec
        else:
            raise ValueError(f"Export URL is not HTTPS: {url}")
        print(f"Export written to: {outfile}")

    def _get_connector_id(self) -> str:
        for connector in self.list_connectors():
            if connector.serviceId == self.connector_name:
                log.debug("connector found", extra={"connector": self.connector_name})
                return connector.id

        return self._create_connector()

    def _create_connector(self) -> str:
        log.info(
            "creating connector",
            extra={"event": "create_connector", "connector": self.connector_name},
        )
        body = {"config": {}, "serviceId": self.connector_name}
        body_str = json.dumps(body)
        connector = self._client.http_post("/v1/connectors", body=body_str)
        return connector["id"]

    def _items_bundle(self, **kwargs) -> ItemsBundleSchema:
        items = {
            self.ACCESS: [],
            self.ASSET: [],
            self.IDENTITY: [],
            self.INHERITANCE_ASSET: [],
            self.INHERITANCE_IDENTITY: [],
            self.SERVICE: [],
        }
        for key in kwargs:
            if key not in items:
                raise ValueError(f"Unknown data type: {key}")
        if kwargs:
            items.update(kwargs)
        return ItemsBundleSchema(**items)


# https://stackoverflow.com/questions/24527006/split-a-generator-into-chunks-without-pre-walking-it/24527424
def _chunk_items(items: Iterator[Any]) -> Iterator[List[Any]]:
    iterator = iter(items)
    for first in iterator:
        yield list(chain([first], islice(iterator, _CHUNK_SIZE - 1)))
