from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import WallboxBLEApiClient, WallboxBLEApiConst
from .const import DOMAIN, LOGGER


class WallboxBLEDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=10),
        )
        self.hass = hass
        self.locked = False
        self.charge_current = 0
        self.max_charge_current = 0
        self.status = ""
        self.status_code = 0
        self.available = False

    @classmethod
    async def create(cls, hass, address):
        self = WallboxBLEDataUpdateCoordinator(hass)
        self.wb = await WallboxBLEApiClient.create(hass, address)
        return self

    async def async_refresh_later(self, delay):
        async def wrap(*_):
            await self.async_refresh()

        async_call_later(self.hass, delay, wrap)

    async def _async_update_data(self):
        if not self.wb.ready:
            return {}

        if self.max_charge_current == 0:
            ok, data = await self.wb.async_get_max_charge_current()
            if ok:
                self.max_charge_current = data
                LOGGER.debug(f"SET {self.max_charge_current=}")

        ok, data = await self.wb.async_get_data()
        if ok:
            LOGGER.debug("Update done")
            self.status_code = data.get("st", 0)
            self.locked = self.status_code == 6
            self.charge_current = data.get("cur", 6)
            self.status = WallboxBLEApiConst.STATUS_CODES[self.status_code]
            self.available = True
            return data
        else:
            self.available = False

    async def async_set_parameter(self, parameter, value):
        ok, _ = await self.wb.request(parameter, value)
        return ok
