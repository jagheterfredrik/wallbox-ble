from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription

from .const import DOMAIN, LOGGER
from .coordinator import WallboxBLEDataUpdateCoordinator
from .entity import WallboxBLEEntity

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="wallbox_ble",
        name="Status",
        # icon="mdi:flash",
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        WallboxBLESensor(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class WallboxBLESensor(WallboxBLEEntity, SensorEntity):
    native_value = 6

    def __init__(
        self,
        coordinator: WallboxBLEDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description

    @property
    def available(self):
        return self.coordinator.available

    @property
    def native_value(self) -> bool:
        return self.coordinator.status
