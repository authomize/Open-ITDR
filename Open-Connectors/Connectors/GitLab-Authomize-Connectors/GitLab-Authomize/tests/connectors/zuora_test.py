from datetime import datetime

from authomize.rest_api_client.generated.schemas import (
    AccessTypes,
    UserStatus,
)

from connectors import zuora


def test_revenue_user_status():
    connector = zuora.Connector()
    connector.current_time = datetime.fromisoformat("2022-01-01T00:00:00")
    default_time = "2015-06-22T00:00:00Z"

    def get_user_dict(start=default_time, end=None, r_start=default_time, r_end=None):
        return {
            "effectivity_start": start,
            "effectivity_end": end,
            "role_effectivity_start": r_start,
            "role_effectivity_end": r_end,
        }

    # User with start dates before current time and no end dates should be enabled
    user = get_user_dict()
    status = connector._revenue_user_status(user)
    assert status == UserStatus.Enabled

    # User with start date after current time and no end dates should be disabled
    user = get_user_dict(start="2022-05-01T00:00:00")
    status = connector._revenue_user_status(user)
    assert status == UserStatus.Disabled

    # User role with start date after current time and no end dates should be disabled
    user = get_user_dict(r_start="2022-05-01T00:00:00")
    status = connector._revenue_user_role_status(user)
    assert status == UserStatus.Disabled

    # User with end date after current time should be enabled
    user = get_user_dict(end="2022-05-01T00:00:00")
    status = connector._revenue_user_status(user)
    assert status == UserStatus.Enabled

    # User role with end date after current time should be enabled
    user = get_user_dict(r_end="2022-05-01T00:00:00")
    status = connector._revenue_user_role_status(user)
    assert status == UserStatus.Enabled

    # User with end date before current time should be disabled
    user = get_user_dict(end="2021-05-01T00:00:00")
    status = connector._revenue_user_status(user)
    assert status == UserStatus.Disabled

    # User role with end date before current time should be disabled
    user = get_user_dict(r_end="2021-05-01T00:00:00")
    status = connector._revenue_user_role_status(user)
    assert status == UserStatus.Disabled
