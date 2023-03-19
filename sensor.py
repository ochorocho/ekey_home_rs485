"""Platform for ekey home rs485 sensor integration."""
from __future__ import annotations

import ipaddress
import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from config.custom_components.ekey_home_rs485.rs485 import socket_connection
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    PLATFORM_SCHEMA
)
from homeassistant.const import ELECTRIC_POTENTIAL_VOLT, CONF_PORT, CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

# Validate configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_IP_ADDRESS): vol.All(ipaddress.ip_address, cv.string),
    vol.Required(CONF_PORT): cv.port,
    vol.Required('user_mapping'): cv.ensure_list,
})

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    users = await hass.auth.async_get_users()
    available_usernames = []
    for user in users:
        if not user.system_generated and user.is_active:
            available_usernames.append(user.name)

    # @todo:
    #       * Add config flow (maybe)
    #       * Fire event
    entities = []
    ekey_config = config.get("user_mapping")

    for ekey in ekey_config:
        ekey_id = ekey["ekey_user_id"]
        username = str(ekey["ha_username"])
        entity_name = username + " (ekey_id:" + str(ekey_id) + ")"
        entities.append(EkeyHomeRs485Sensor(entity_name, ekey_id, username, SensorDeviceClass))

    async_add_entities(entities)

    # Create task outside the event loop
    hass.async_create_task(socket_connection(hass, config))


class EkeyHomeRs485Sensor(SensorEntity):
    """Representation of a EkeyHomeRs485 Sensor."""

    def __init__(self, name: str, ekey_id: str, username: str, device_class) -> None:
        self.username = username
        self.ekey_id = ekey_id

        # Will also be used as Entity ID
        self._attr_name = name
        self._available = True

    @property
    def available(self):
        """Return if projector is available."""

        return self._available

    def update(self) -> None:
        """Fetch data - get the state set in 'set_state'"""
        #_LOGGER.error(self.hass.states.get(self.entity_id).state)
        self._attr_native_value = self.hass.states.get(self.entity_id).state
