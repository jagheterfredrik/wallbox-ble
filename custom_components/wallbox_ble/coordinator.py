from __future__ import annotations

from datetime import timedelta

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import WallboxBLEApiClient
from .const import DOMAIN, LOGGER


class WallboxBLEDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        address: str,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=10),
        )
        self.address = address
        self.locked = False
    
    @classmethod
    async def create(cls, hass, address):
        self = WallboxBLEDataUpdateCoordinator(hass, address)
        self.device = async_ble_device_from_address(self.hass, self.address, connectable=True)
        self.wb = await WallboxBLEApiClient.create(self.device)
        return self

    async def _async_update_data(self):
        val = await self.wb.async_get_data()
        LOGGER.debug("Update done")
        self.locked = val.get("st", 0) == 6
        return val

    async def async_set_locked(self, locked):
        resp = await self.wb.async_set_locked(locked)
        if resp:
            self.locked = locked
            LOGGER.debug("Lock done")
