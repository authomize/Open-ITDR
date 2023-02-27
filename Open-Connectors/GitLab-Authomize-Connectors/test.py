"""Test module used for local development."""
import datetime as dt

from authomize.rest_api_client import (
    AccessDescription,
    AccessTypes,
    AssetDescription,
    AssetTypes,
    IdentityDescription,
    IdentityTypes,
    UserStatus,
)

from connectors import Base
from logger import logger as log


# pylint: disable=no-self-use
class Test:
    """Test commands for development."""

    def log_error(self) -> None:
        """Log a test message at ERROR level."""
        log.error("Test message at ERROR level.")

    def log_fatal(self) -> None:
        """Log a test message at FATAL level."""
        log.fatal("Test message at FATAL level.")

    def connector(self) -> None:
        """Write TestConnector data to Authomize."""
        FakeConnector().run()


class FakeConnector(Base):
    """Fake Connector for testing."""

    APP_ID = 42
    test_connector = True

    def __init__(self) -> None:
        super().__init__("TestConnector")

    def collect(self) -> dict:
        result = {}
        result[Base.ASSET] = [
            AssetDescription(
                id=self.APP_ID,
                name="TestConnector",
                type=AssetTypes.Application,
            ),
        ]
        result[Base.IDENTITY] = [
            IdentityDescription(
                id="1",
                name="Morgan Manager",
                type=IdentityTypes.User,
                email="morgan@example.com",
                createdAt=dt.datetime(2020, 1, 1),
                status=UserStatus.Enabled,
            ),
            IdentityDescription(
                id="2",
                name="Drew Developer",
                type=IdentityTypes.User,
                email="drew@example.com",
                manager="1",
                createdAt=dt.datetime(2020, 1, 2),
                status=UserStatus.Enabled,
            ),
            IdentityDescription(
                id="3",
                name="Taylor Terminated",
                type=IdentityTypes.User,
                email="taylor@example.com",
                manager="1",
                createdAt=dt.datetime(2020, 1, 3),
                terminationDate=dt.datetime(2020, 2, 3),
                status=UserStatus.Disabled,
            ),
        ]
        result[Base.ACCESS] = [
            AccessDescription(
                fromIdentityId="1",
                toAssetId=self.APP_ID,
                accessType=AccessTypes.Administrative,
            ),
            AccessDescription(
                fromIdentityId="2",
                toAssetId=self.APP_ID,
                accessType=AccessTypes.Write,
            ),
            AccessDescription(
                fromIdentityId="3",
                toAssetId=self.APP_ID,
                accessType=AccessTypes.Read,
            ),
        ]
        return result
