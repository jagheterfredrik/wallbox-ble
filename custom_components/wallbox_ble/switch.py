from __future__ import annotations

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription

from .api import WallboxBLEApiConst
from .const import DOMAIN, LOGGER
from .coordinator import WallboxBLEDataUpdateCoordinator
from .entity import WallboxBLEEntity

ENTITY_DESCRIPTIONS = (
    SwitchEntityDescription(
        key="wallbox_ble",
        name="Charge",
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        WallboxBLESwitch(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class WallboxBLESwitch(WallboxBLEEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: WallboxBLEDataUpdateCoordinator,
        entity_description: SwitchEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description

    @property
    def available(self):
        return self.coordinator.available and self.coordinator.status_code in (1, 4)

    @property
    def is_on(self) -> bool:
        return self.coordinator.status_code == 1

    async def async_turn_on(self, **_: any) -> None:
        await self.coordinator.async_set_parameter(WallboxBLEApiConst.START_STOP_CHARGING, 1)
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **_: any) -> None:
        await self.coordinator.async_set_parameter(WallboxBLEApiConst.START_STOP_CHARGING, 0)
        await self.coordinator.async_refresh()
