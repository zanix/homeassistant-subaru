"""Test Subaru sensors."""
from unittest.mock import patch

import pytest

from custom_components.subaru.const import FETCH_INTERVAL
from custom_components.subaru.sensor import (
    API_GEN_2_SENSORS,
    DOMAIN as SUBARU_DOMAIN,
    EV_SENSORS,
    SAFETY_SENSORS,
)
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.util import slugify
from homeassistant.util.unit_system import IMPERIAL_SYSTEM

from .api_responses import (
    EXPECTED_STATE_EV_IMPERIAL,
    EXPECTED_STATE_EV_METRIC,
    EXPECTED_STATE_EV_UNAVAILABLE,
    TEST_VIN_2_EV,
    VEHICLE_STATUS_EV,
)
from .conftest import (
    MOCK_API_FETCH,
    MOCK_API_GET_DATA,
    TEST_DEVICE_NAME,
    advance_time,
    migrate_unique_ids,
    migrate_unique_ids_duplicate,
)


async def test_sensors_ev_imperial(hass, ev_entry):
    """Test sensors supporting imperial units."""
    hass.config.units = IMPERIAL_SYSTEM

    with patch(MOCK_API_FETCH), patch(
        MOCK_API_GET_DATA, return_value=VEHICLE_STATUS_EV
    ):
        advance_time(hass, FETCH_INTERVAL)
        await hass.async_block_till_done()

    _assert_data(hass, EXPECTED_STATE_EV_IMPERIAL)


async def test_sensors_ev_metric(hass, ev_entry):
    """Test sensors supporting metric units."""
    _assert_data(hass, EXPECTED_STATE_EV_METRIC)


async def test_sensors_missing_vin_data(hass, ev_entry):
    """Test for missing VIN dataset."""
    with patch(MOCK_API_FETCH), patch(MOCK_API_GET_DATA, return_value=None):
        advance_time(hass, FETCH_INTERVAL)
        await hass.async_block_till_done()

    _assert_data(hass, EXPECTED_STATE_EV_UNAVAILABLE)


@pytest.mark.parametrize(
    "entitydata,old_unique_id,new_unique_id",
    [
        (
            {
                "domain": SENSOR_DOMAIN,
                "platform": SUBARU_DOMAIN,
                "unique_id": f"{TEST_VIN_2_EV}_{API_GEN_2_SENSORS[0].name}",
            },
            f"{TEST_VIN_2_EV}_{API_GEN_2_SENSORS[0].name}",
            f"{TEST_VIN_2_EV}_{API_GEN_2_SENSORS[0].key}",
        ),
    ],
)
async def test_sensor_migrate_unique_ids(
    hass, entitydata, old_unique_id, new_unique_id, subaru_config_entry
) -> None:
    """Test successful migration of entity unique_ids."""
    await migrate_unique_ids(
        hass, entitydata, old_unique_id, new_unique_id, subaru_config_entry
    )


@pytest.mark.parametrize(
    "entitydata,old_unique_id,new_unique_id",
    [
        (
            {
                "domain": SENSOR_DOMAIN,
                "platform": SUBARU_DOMAIN,
                "unique_id": f"{TEST_VIN_2_EV}_{API_GEN_2_SENSORS[0].name}",
            },
            f"{TEST_VIN_2_EV}_{API_GEN_2_SENSORS[0].name}",
            f"{TEST_VIN_2_EV}_{API_GEN_2_SENSORS[0].key}",
        )
    ],
)
async def test_sensor_migrate_unique_ids_duplicate(
    hass, entitydata, old_unique_id, new_unique_id, subaru_config_entry
) -> None:
    """Test unsuccessful migration of entity unique_ids due to duplicate."""
    await migrate_unique_ids_duplicate(
        hass, entitydata, old_unique_id, new_unique_id, subaru_config_entry
    )


def _assert_data(hass, expected_state):
    sensor_list = EV_SENSORS
    sensor_list.extend(API_GEN_2_SENSORS)
    sensor_list.extend(SAFETY_SENSORS)
    expected_states = {}
    for item in sensor_list:
        expected_states[
            f"sensor.{slugify(f'{TEST_DEVICE_NAME} {item.name}')}"
        ] = expected_state[item.key]

    for sensor, value in expected_states.items():
        actual = hass.states.get(sensor)
        assert actual.state == value
