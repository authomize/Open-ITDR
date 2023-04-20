from unittest.mock import patch

from authomize.rest_api_client.generated.schemas import (
    AccessTypes,
    UserStatus,
)

from connectors import ava_tax
from tests.helpers import Fixture

fix = Fixture("ava_tax")


# class AvaTaxMock:
class _QueryUsers:
    def json(self) -> dict:
        return fix.read_json("users")


@patch.object(ava_tax.AvataxClient, "query_users")
def test_collect(mock):
    mock.side_effect = _QueryUsers
    connector = ava_tax.Connector()
    items = connector.collect()
    assert len(items) == 3

    assets = items[connector.ASSET]
    assert len(assets) == 1

    access = items[connector.ACCESS]
    assert len(access) == 3

    identites = items[connector.IDENTITY]
    assert len(identites) == 3

    assert access[0].accessType == AccessTypes.Administrative
    assert access[0].accessName == "Account administrator"

    assert access[1].accessType == AccessTypes.Write
    assert access[1].accessName == "Limited access account user"

    assert access[2].accessType == AccessTypes.Administrative
    assert access[2].accessName == "Account administrator"

    assert identites[0].status == UserStatus.Disabled
    assert identites[1].status == UserStatus.Enabled
    assert identites[2].status == UserStatus.Enabled
