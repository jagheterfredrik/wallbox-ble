from __future__ import annotations

from homeassistant.components.lock import LockEntity, LockEntityDescription

from .api import WallboxBLEApiConst
from .const import DOMAIN, LOGGER
from .coordinator import WallboxBLEDataUpdateCoordinator
from .entity import WallboxBLEEntity

ENTITY_DESCRIPTIONS = (
    LockEntityDescription(
        key="wallbox_ble",
        name="Lock",
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        WallboxBLELock(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class WallboxBLELock(WallboxBLEEntity, LockEntity):
    def __init__(
        self,
        coordinator: WallboxBLEDataUpdateCoordinator,
        entity_description: LockEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description

    @property
    def available(self):
        return self.coordinator.available

    @property
    def is_locked(self) -> bool:
        return self.coordinator.locked

    async def async_lock(self, **_: any) -> None:
        if await self.coordinator.async_set_parameter(WallboxBLEApiConst.LOCK, 1):
            self.coordinator.locked = True
            self.async_schedule_update_ha_state()  # Locking is slow, so we fake it
            await self.coordinator.async_refresh_later(1)

    async def async_unlock(self, **_: any) -> None:
        if await self.coordinator.async_set_parameter(WallboxBLEApiConst.LOCK, 0):
            self.coordinator.locked = False
            self.async_schedule_update_ha_state()  # Unlocking is even slower, so we fake it
            await self.coordinator.async_refresh_later(1)
