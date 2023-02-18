from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberEntityDescription

from .api import WallboxBLEApiConst
from .const import DOMAIN, LOGGER
from .coordinator import WallboxBLEDataUpdateCoordinator
from .entity import WallboxBLEEntity

ENTITY_DESCRIPTIONS = (
    NumberEntityDescription(
        key="wallbox_ble",
        name="Charge current",
        native_min_value=6,
        device_class=NumberDeviceClass.CURRENT,
        icon="mdi:flash",
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        WallboxBLENumber(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class WallboxBLENumber(WallboxBLEEntity, NumberEntity):
    def __init__(
        self,
        coordinator: WallboxBLEDataUpdateCoordinator,
        entity_description: NumberEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description

    @property
    def available(self):
        return self.coordinator.available

    @property
    def native_value(self) -> bool:
        return self.coordinator.charge_current

    @property
    def native_max_value(self):
        return self.coordinator.max_charge_current

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_parameter(WallboxBLEApiConst.SET_MAX_CHARGING_CURRENT, int(value))
        await self.coordinator.async_refresh()
