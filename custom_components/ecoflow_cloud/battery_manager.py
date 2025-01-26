from __future__ import annotations

import logging
import json

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

class BatterySensorManager:
    def __init__(self, add_entities_callback: AddEntitiesCallback, device, coordinator):
        self._add_entities = add_entities_callback
        self._device = device
        self._coordinator = coordinator
        self._battery_sensors: dict[str, BatteryModuleSensor] = {}

    def process_quota_data(self, raw_params: dict[str, any]):
        _LOGGER.debug(f"BatterySensorManager.process_quota_data => got {len(raw_params)} keys")
        for key, val in raw_params.items():
            if not key.startswith("bp_addr."):
                continue
            if key in self._battery_sensors:
                continue

            _LOGGER.info(f"Discovered new Battery Module {key}")
            sensor_entity = BatteryModuleSensor(self._device, self._coordinator, key)
            self._battery_sensors[key] = sensor_entity
            self._add_entities([sensor_entity])

    def update_existing_sensors(self):
        for sensor in self._battery_sensors.values():
            sensor.update_from_coordinator()

class BatteryModuleSensor(Entity):
    def __init__(self, device, coordinator, battery_key: str):
        self._device = device
        self._coordinator = coordinator
        self._battery_key = battery_key  # z.B. "bp_addr.HJ32ZDH4ZF7E0051"
        self._attrs = {}
        self._state = None
        self._unique_id = f"{device.device_info.sn}-{battery_key}"

    @property
    def name(self) -> str:
        return f"{self._device.device_info.name} {self._battery_key}"

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def extra_state_attributes(self):
        return self._attrs

    @property
    def state(self):
        return self._state

    def update_from_coordinator(self):
        params = self._device.data.params
        _LOGGER.debug(f"BatteryModuleSensor.update_from_coordinator called for {self._battery_key}")
        main_soc_key = f"{self._battery_key}.bpSoc"
        self._state = params.get(main_soc_key, "unknown")
        _LOGGER.debug(f"Setting state for {self.name}: {self._state}")

        soh_key = f"{self._battery_key}.bpSoh"
        cyc_key = f"{self._battery_key}.bpCycles"
        if soh_key in params:
            self._attrs["bpSoh"] = params[soh_key]
            _LOGGER.debug(f"Setting bpSoh for {self.name}: {self._attrs['bpSoh']}")
        if cyc_key in params:
            self._attrs["bpCycles"] = params[cyc_key]
            _LOGGER.debug(f"Setting bpCycles for {self.name}: {self._attrs['bpCycles']}")

        temp_key = f"{self._battery_key}.bpTemp"
        if temp_key in params:
            self._attrs["bpTemp"] = params[temp_key]
            _LOGGER.debug(f"Setting bpTemp for {self.name}: {self._attrs['bpTemp']}")

        self.schedule_update_ha_state()

    def update(self):
        self.update_from_coordinator()
