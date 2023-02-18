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
        self.charge_current = 0
        self.max_charge_current = 0
        self.available = False
    
    @classmethod
    async def create(cls, hass, address):
        self = WallboxBLEDataUpdateCoordinator(hass, address)
        self.device = async_ble_device_from_address(self.hass, self.address, connectable=True)
        self.wb = await WallboxBLEApiClient.create(self.device)
        return self

    async def _async_update_data(self):
        if self.max_charge_current == 0:
            ok, data = await self.wb.async_get_max_charge_current()
            if ok:
                self.max_charge_current = data
                LOGGER.debug(f"SET {self.max_charge_current=}")

        ok, data = await self.wb.async_get_data()
        if ok:
            LOGGER.debug("Update done")
            self.locked = data.get("st", 0) == 6
            self.charge_current = data.get("cur", 6)
            self.available = True
            return data
        else:
            self.available = False

    async def async_set_locked(self, locked):
        resp = await self.wb.async_set_locked(locked)
        if resp:
            self.locked = locked
            LOGGER.debug("Lock done")

    async def async_set_charge_current(self, charge_current):
        resp = await self.wb.async_set_charge_current(int(charge_current))
        if resp:
            self.charge_current = charge_current
            LOGGER.debug("Set current done")
