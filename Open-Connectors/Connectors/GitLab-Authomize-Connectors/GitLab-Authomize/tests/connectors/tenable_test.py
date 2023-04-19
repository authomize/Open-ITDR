from unittest.mock import patch, PropertyMock

from authomize.rest_api_client.generated.schemas import (
    AccessTypes,
    UserStatus,
)

from connectors import tenable
from tests.helpers import Fixture

fix = Fixture("tenable")


@patch.object(tenable.TenableIO, "users", new_callable=PropertyMock)
def test_collect(mock):
    mock.return_value.list.return_value = fix.read_json("users")
    connector = tenable.Connector()
    items = connector.collect()
    assert len(items) == 3

    assets = items[connector.ASSET]
    assert len(assets) == 1

    access = items[connector.ACCESS]
    assert len(access) == 3

    identites = items[connector.IDENTITY]
    assert len(identites) == 3

    assert access[0].accessType == AccessTypes.Read
    assert access[0].accessName == "Basic"

    assert access[1].accessType == AccessTypes.Administrative
    assert access[1].accessName == "Administrator"

    assert access[2].accessType == AccessTypes.Create
    assert access[2].accessName == "Scan Manager"

    assert identites[0].hasTwoFactorAuthenticationEnabled is False
    assert identites[1].hasTwoFactorAuthenticationEnabled is False
    assert identites[2].hasTwoFactorAuthenticationEnabled is True

    assert identites[0].status == UserStatus.Disabled
    assert identites[1].status == UserStatus.Disabled
    assert identites[2].status == UserStatus.Enabled
