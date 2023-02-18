"""Wallbox BLE API Client."""
from __future__ import annotations

import random
import asyncio
import json
import contextlib
from bleak import BleakClient
from bleak_retry_connector import establish_connection

from .const import LOGGER

UART_SERVICE_UUID = "331a36f5-2459-45ea-9d95-6142f0c4b307"
UART_RX_CHAR_UUID = "a9da6040-0823-4995-94ec-9ce41ca28833"
UART_TX_CHAR_UUID = "a73e9a10-628f-4494-a099-12efaf72258f"

GET_AUTOLOCK = "g_alo"
GET_BATTERY_CONFIG = "r_socr"
GET_CHARGER_VERSIONS = "fw_v_"
GET_DISCHARGE_SESSION = "r_dis"
GET_DYNAMIC_GRID_CODE = "ggcds"
GET_DYNAMIC_GRID_CODE_REGULATIONS = "r_gcdl"
GET_DYNAMIC_GRID_CODE_FEATURES = "r_gcdf"
GET_DYNAMIC_GRID_CODE_LOGS = "r_gcli"
GET_DYNAMIC_GRID_CODE_LOGS_DETAIL = "r_gcld"
GET_DYNAMIC_GRID_CODE_LOGS_SIZE = "r_gcls"
GET_DYNAMIC_GRID_CODE_ALERT = "r_gcai"
GET_DYNAMIC_GRID_CODE_ALERT_SIZE = "r_gcas"
GET_ECO_SMART_CONFIGURATION = "g_ecos"
GET_GESTURE_CONFIGURATION = "ggsta"
GET_GRID_CODE = "r_gcd"
GET_HALO_CONFIG = "g_halocfg"
GET_HOTSPOT_UPDATE_STATUS = "r_hup"
GET_IP_MODE = "gimod"
GET_LOCK_STATUS = "r_lck"
GET_MAC_ADDRESSES = "g_mac"
GET_MAX_AVAILABLE_CURRENT = "r_fsI"
GET_MID_CONFIGURATION = "g_mid"
GET_MOBILE_CONNECTIVITY = "gmcon"
GET_NETWORKS_STATUS = "gnsta"
GET_OCPP = "g_ocpp"
GET_POWER_BOOST = "r_hsh"
GET_POWER_BOOST_STATUS = "r_dca"
GET_POWER_INFUSION = "g_pwi"
GET_POWER_SHARING = "g_psh"
GET_PROXY_MODE = "gpmod"
GET_SCHEDULE = "r_sch"
GET_SERIAL_NUMBER = "r_sn_"
GET_SESSIONS_INFO = "r_ses"
GET_SESSION = "r_log"
GET_STATUS = "r_dat"
GET_TIMEZONE = "g_tzn"
GET_GROUNDING_STATUS = "r_wel"
GET_WIFI_NETWORKS = "gwnet"
GET_WIFI_STATUS = "gwsta"
LOCK = "w_lck"
REBOOT = "rebot"
SET_AUTOLOCK = "s_alo"
SET_BATTERY_CONFIG = "w_socr"
SEND_TRANSACTION_DATA = "w_td"
SET_DATA_TRANSACTION_STATUS = "s_dts"
SET_DYNAMIC_GRID_CODE = "sgcds"
SET_DYNAMIC_GRID_CODE_REGULATION = "w_gcdr"
SET_DYNAMIC_GRID_CODE_FEATURE = "w_gcdf"
SET_ECO_SMART_CONFIGURATION = "s_ecos"
SET_GESTURE_CONFIGURATION = "sgsta"
SET_GRID_CODE = "w_gcd"
SET_HALO_CONFIG = "s_halocfg"
SET_HOTSPOT_UPDATE = "s_hup"
SET_HOTSPOT_UPDATE_INFO = "s_deb"
SET_IP_MODE = "simod"
SET_MAX_CHARGING_CURRENT = "w_mxI"
SET_MID_CONFIGURATION = "s_mid"
SET_MOBILE_CONNECTIVITY = "smcon"
SET_MOBILE_CONNECTIVITY_STATUS = "smcen"
SET_MULTIUSER = "s_mus"
SET_OCPP = "s_ocpp"
SET_POWER_BOOST = "w_hsh"
SET_POWER_INFUSION = "s_pwi"
SET_POWER_SHARING = "s_psh"
SET_PROXY_MODE = "spmod"
SET_SCHEDULE = "w_sch"
SET_TIME = "Wtime"
SET_TIMEZONE = "s_tzn"
SET_USER = "suser"
SET_USER_LIST = "sulis"
SET_GROUNDING_STATUS = "w_wel"
SET_WIFI = "swcon"
SET_WIFI_STATUS = "swsta"
SOFTWARE_CHECK = "gupdc"
START_STOP_CHARGING = "w_cha"
UNLOCK_MOBILE_SIM = "smpuk"
UPDATE_SOFTWARE_PROGRESS = "supdp"
UPDATE_SOFTWARE = "supds"

class WallboxBLEApiClient:
    async def run_ble_client(self, device):
        async def callback_handler(sender, data):
            await self.rx_queue.put(data)

        disconnected_event = asyncio.Event()
        
        def disconnected_callback(client):
            LOGGER.debug("Disconnected!")
            disconnected_event.set()

        while True:
            LOGGER.debug("Connecting...")

            try:
                async with BleakClient(device, disconnected_callback=disconnected_callback) as self.client:
                    LOGGER.debug(f"Connected!")
                    await self.client.start_notify(UART_TX_CHAR_UUID, callback_handler)
                    await disconnected_event.wait()
            except Exception as e:
                LOGGER.debug(f"Error: {type(e)}, {e}")
                await asyncio.sleep(1.0)

            self.client = None
            disconnected_event.clear()

    async def connection_established(self):
        while True:
            if self.client and self.client.is_connected:
                return
            asyncio.sleep(0.1)

    @classmethod
    async def create(cls, device):
        self = WallboxBLEApiClient()
        self.client = None
        self.rx_queue = asyncio.Queue()
        self.client_task = asyncio.create_task(self.run_ble_client(device))
        return self

    async def get_parsed_response(self, request_id):
        data = bytearray()
        while True:
            try:
                data += await self.rx_queue.get()
                parsed_data = json.loads(data)
                LOGGER.debug(f"Got {parsed_data=}")
                if parsed_data["id"] == request_id:
                    return parsed_data.get("r")
                else:
                    data = bytearray()
            except:
                pass

    def clear_rx_queue(self):
        self.rx_queue = asyncio.Queue()

    async def request(self, method, parameter=None):
        if not self.client or not self.client.is_connected:
            LOGGER.debug(f"NOT CONNECTED! {self.client}")
            return {}

        request_id = random.randint(1, 999)

        uart_service = self.client.services.get_service(UART_SERVICE_UUID)
        rx_char = uart_service.get_characteristic(UART_RX_CHAR_UUID)

        payload = { "met": method, "par": parameter, "id": request_id }

        data = json.dumps(payload, separators=[",", ":"])
        data = bytes(data, "utf8")
        data = b"EaE" + bytes([len(data)]) + data
        data = data + bytes([sum(c for c in data) % 256])

        self.clear_rx_queue()
        await self.client.write_gatt_char(rx_char, data, True)

        try:
            response = await asyncio.wait_for(self.get_parsed_response(request_id), 2)
            LOGGER.debug("Got response!")
            return response
        except asyncio.TimeoutError:
            LOGGER.debug("No response!")
            return {}

    async def async_get_data(self) -> any:
        """Get data from the API."""
        return await self.request(GET_STATUS)

    async def async_set_locked(self, locked: bool) -> any:
        """Get data from the API."""
        return await self.request(LOCK, 1 if locked else 0) == None

    async def async_get_max_charge_current(self) -> any:
        """Get data from the API."""
        return await self.request(GET_MAX_AVAILABLE_CURRENT)

    async def async_set_charge_current(self, current) -> any:
        """Get data from the API."""
        return await self.request(SET_MAX_CHARGING_CURRENT, current) == None
