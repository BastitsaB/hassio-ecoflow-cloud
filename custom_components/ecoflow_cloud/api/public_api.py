import hashlib
import hmac
import logging
import random
import time
from datetime import datetime

import aiohttp
from homeassistant.util import dt

from . import EcoflowApiClient
from ..devices import DiagnosticDevice, EcoflowDeviceInfo

_LOGGER = logging.getLogger(__name__)

BASE_URI = "https://api-e.ecoflow.com/iot-open/sign"

# Client ID limits for MQTT connections:
# Only 10 unique client IDs are allowed per day. 
# It's recommended to use a static client_id for your application.

class EcoflowPublicApiClient(EcoflowApiClient):
    def __init__(self, access_key: str, secret_key: str, group: str):
        super().__init__()
        self.access_key = access_key
        self.secret_key = secret_key
        self.group = group
        # nonce/timestamp werden NICHT mehr im Konstruktor erzeugt
        # sondern pro Request frisch in call_api()

    async def login(self):
        _LOGGER.info("Requesting IoT MQTT credentials")
        # Ruft die Zertifizierungs-API auf, um MQTT-Daten zu erhalten
        response = await self.call_api("/certification")
        self._accept_mqqt_certification(response)

        # client_id möglichst stabil wählen
        self.mqtt_info.client_id = f"Hassio-{self.mqtt_info.username}-{self.group.replace(' ', '-')}"

    async def fetch_all_available_devices(self) -> list[EcoflowDeviceInfo]:
        _LOGGER.info("Requesting all devices")
        response = await self.call_api("/device/list")
        result = []
        for device in response["data"]:
            sn = device["sn"]
            product_name = device.get("productName", "EcoFlowDevice")  # KeyError vermeiden
            device_name = device.get("deviceName", f"{product_name}-{sn}")
            status = int(device["online"])
            result.append(self.__create_device_info(sn, device_name, product_name, status))
        return result

    def configure_device(self, device_sn: str, device_name: str, device_type: str, power_step=-1):
        info = self.__create_device_info(device_sn, device_name, device_type)

        from custom_components.ecoflow_cloud.devices.registry import device_by_product
        if device_type in device_by_product:
            device = device_by_product[device_type](info)
        else:
            device = DiagnosticDevice(info)

        device.power_step = power_step
        self.add_device(device)
        return device

    async def quota_all(self, device_sn: str | None):
        if not device_sn:
            target_devices = self.devices.keys()
            # update all statuses
            devices = await self.fetch_all_available_devices()
            for dev in devices:
                if dev.sn in self.devices:
                    self.devices[dev.sn].data.update_status({"params": {"status": dev.status}})
        else:
            target_devices = [device_sn]

        for sn in target_devices:
            raw = await self.call_api("/device/quota/all", {"sn": sn})
            if "data" in raw:
                self.devices[sn].data.update_data({"params": raw["data"]})

    async def call_api(self, endpoint: str, params: dict[str, str] = None) -> dict:
        # Erzeuge pro Request neuen nonce & timestamp
        nonce = str(random.randint(10000, 1000000))
        timestamp = str(int(time.time() * 1000))

        async with aiohttp.ClientSession() as session:
            params_str = ""
            if params is not None:
                params_str = self.__sort_and_concat_params(params)

            sign = self.__gen_sign(params_str, nonce, timestamp)

            headers = {
                'accessKey': self.access_key,
                'nonce': nonce,
                'timestamp': timestamp,
                'sign': sign
            }

            url = f"{BASE_URI}{endpoint}?{params_str}"
            resp = await session.get(url, headers=headers)

            # **Ab hier: raw Text loggen**
            raw_text = await resp.text()
            _LOGGER.debug(f"[call_api] Raw response from {endpoint}: {raw_text}")

            # Dann JSON parsen
            if resp.status != 200:
                raise EcoflowException(f"Got HTTP status code {resp.status}: {resp.reason}")

            try:
                json_resp = await resp.json()
            except Exception as error:
                raise EcoflowException(f"Failed to parse JSON: {error}")

            # Hier evtl. noch mal loggen, wenn du möchtest
            _LOGGER.debug(f"[call_api] Parsed JSON from {endpoint}: {json_resp}")

            return json_resp

    def __create_device_info(self, device_sn: str, device_name: str,
                             device_type: str, status: int = -1) -> EcoflowDeviceInfo:
        return EcoflowDeviceInfo(
            public_api=True,
            sn=device_sn,
            name=device_name,
            device_type=device_type,
            status=status,
            data_topic=f"/open/{self.mqtt_info.username}/{device_sn}/quota",
            set_topic=f"/open/{self.mqtt_info.username}/{device_sn}/set",
            set_reply_topic=f"/open/{self.mqtt_info.username}/{device_sn}/set_reply",
            get_topic=None,
            get_reply_topic=None,
            status_topic=f"/open/{self.mqtt_info.username}/{device_sn}/status"
        )

    def __gen_sign(self, query_params: str | None, nonce: str, timestamp: str) -> str:
        # Basisstring: Query + accessKey + nonce + timestamp
        base_str = f"accessKey={self.access_key}&nonce={nonce}&timestamp={timestamp}"
        if query_params:
            base_str = query_params + "&" + base_str

        return self.__encrypt_hmac_sha256(base_str, self.secret_key)

    def __sort_and_concat_params(self, params: dict[str, str]) -> str:
        # Sortiere die Params nach Key und baue "key=value" Paare
        sorted_items = sorted(params.items(), key=lambda x: x[0])
        param_strings = [f"{key}={value}" for key, value in sorted_items]
        return "&".join(param_strings)

    def __encrypt_hmac_sha256(self, message: str, secret_key: str) -> str:
        message_bytes = message.encode('utf-8')
        secret_bytes = secret_key.encode('utf-8')

        hmac_obj = hmac.new(secret_bytes, message_bytes, hashlib.sha256)
        return hmac_obj.hexdigest()
