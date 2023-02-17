"""Wallbox BLE API Client."""
from __future__ import annotations

import random
import asyncio
import json
import contextlib
from bleak import BleakClient
from bleak_retry_connector import establish_connection

UART_SERVICE_UUID = "331a36f5-2459-45ea-9d95-6142f0c4b307"
UART_RX_CHAR_UUID = "a9da6040-0823-4995-94ec-9ce41ca28833"
UART_TX_CHAR_UUID = "a73e9a10-628f-4494-a099-12efaf72258f"

class WallboxBLEApiClient:
    """Sample API Client."""

    async def ensure_client(self):
        if self.client:
            return
        self.client = await establish_connection(BleakClient, self.device, self.device.address, self.handle_disconnect)
        await self.client.start_notify(UART_TX_CHAR_UUID, self.handle_rx)

    @classmethod
    async def create(cls, device):
        self = WallboxBLEApiClient()
        self.device = device
        self.client = None
        await self.ensure_client()
        return self

    def handle_disconnect(self, _: BleakClient):
        self.client = None

    def handle_rx(self, _: BleakGATTCharacteristic, data: bytearray):
        self.all_data += data
        try:
            parsed_data = json.loads(self.all_data)
            if parsed_data["id"] == self.request_id:
                self.response = parsed_data.get("r")
                self.evt.set()
        except:
            pass

    async def execute(self, method, parameter=None):
        self.ensure_client()

        self.all_data = bytearray()
        self.request_id = random.randint(1, 999)
        self.evt = asyncio.Event()
        self.response = {}

        nus = self.client.services.get_service(UART_SERVICE_UUID)
        rx_char = nus.get_characteristic(UART_RX_CHAR_UUID)

        payload = { "met": method, "par": parameter, "id": self.request_id }

        data = json.dumps(payload, separators=[",", ":"])
        data = bytes(data, "utf8")
        data = b"EaE" + bytes([len(data)]) + data
        data = data + bytes([sum(c for c in data) % 256])

        await self.client.write_gatt_char(rx_char, data, True)

        try:
            await asyncio.wait_for(self.evt.wait(), 2)
            return self.response
        except asyncio.TimeoutError:
            return None


    async def async_get_data(self) -> any:
        """Get data from the API."""
        return await self.execute("r_lck")

    async def async_set_locked(self, locked: bool) -> any:
        """Get data from the API."""
        return await self.execute("w_lck", 1 if locked else 0) == 0
