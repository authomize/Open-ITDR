from datetime import datetime
from unittest.mock import patch

from authomize.rest_api_client.generated.schemas import (
    BundleTransactionSchema,
    RestApiConnectorListSchema,
    SubmitResponse,
)

import connectors
from logger import logger
from connectors.test import FakeConnector
from tests.helpers import Fixture

_CONNECTOR_ID = "1234"
_TRANSACTION_ID = "123"


fix = Fixture("authomize")


class AuthomizeMock:
    def __init__(self, **kwargs):
        self.requests = {}

    def list_connectors(self, **kwargs):
        data = fix.read_json("list_connectors")
        return RestApiConnectorListSchema(**data)

    def create_transaction(self, *args):
        data = fix.read_json("begin_transaction")
        return BundleTransactionSchema(**data)

    def apply_transaction(self, *args):
        data = fix.read_json("begin_transaction")
        return BundleTransactionSchema(**data)

    def extend_transaction_items(self, *args):
        return SubmitResponse(acceptedTimestamp=datetime.now().isoformat())

    def retrieve_transaction(self, connector_id, transaction_id):
        data = fix.read_json("begin_transaction")
        attempt = self.requests.get("retrieve_transaction", 0)
        if attempt == 0:
            data["state"] = "Ingest"
        if attempt == 1:
            data["state"] = "PostProcess"
        if attempt == 2:
            data["state"] = "Complete"
        self.requests["retrieve_transaction"] = attempt + 1
        return BundleTransactionSchema(**data)

    def http_post(self, url, **kwargs):
        if url == "/v1/connectors":
            return fix.read_json("create_connector")

    def phony(self, *args, **kwargs):
        pass

    def exp(self, *args, **kwargs):
        raise Exception("fake exception")


@patch.object(connectors.Client, "list_connectors", AuthomizeMock().list_connectors)
def test_list_connectors():
    base = connectors.Base("base")
    conns = list(base.list_connectors())
    assert len(conns) == 3


@patch.object(connectors.Client, "list_connectors")
@patch.object(connectors.Client, "create_transaction")
@patch.object(connectors.Client, "apply_transaction")
@patch.object(connectors.Client, "extend_transaction_items")
@patch.object(connectors.Client, "retrieve_transaction")
@patch.object(connectors.Client, "http_post")
def test_run(*mocks):
    mock = AuthomizeMock()

    mocks[0].side_effect = mock.http_post
    mocks[1].side_effect = mock.retrieve_transaction
    mocks[2].side_effect = mock.extend_transaction_items
    mocks[3].side_effect = mock.apply_transaction
    mocks[4].side_effect = mock.create_transaction
    mocks[5].side_effect = mock.list_connectors

    connectors._APPLY_BACKOFF = 0  # no need to wait for external API
    conn = FakeConnector()
    conn.run()

    for m in mocks:
        m.assert_called()


@patch.object(connectors.Client, "list_connectors", AuthomizeMock().exp)
def test_run_error(caplog):
    with patch.object(logger.logger, "propagate", True):
        conn = FakeConnector()
        conn.run()
        assert "fake exception" in caplog.text


@patch.object(connectors.Client, "http_get", side_effect=AuthomizeMock().phony)
@patch.object(connectors.Client, "http_post", side_effect=AuthomizeMock().phony)
def test_run_testing_mode(mock_post, mock_get):
    with patch.object(connectors.Base, "test", True):
        conn = FakeConnector()
        conn.run()

        # Test mode should not make calls to authomize
        mock_get.assert_not_called()
        mock_post.assert_not_called()
