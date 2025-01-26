# ecoflow_cloud/battery_manager.py

import logging
from typing import Any, Dict

from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .entities import BaseSensorEntity
from .sensor import BatteryModuleSensor

_LOGGER = logging.getLogger(__name__)

class BatterySensorManager:
    """
    Verwalte dynamisch Sensoren pro Battery-SN (z.B. bp_addr.HJ32ZDH4XYZ...).
    """

    def __init__(self, add_entities_callback: AddEntitiesCallback, device: Any, coordinator: Any):
        self._add_entities = add_entities_callback
        self._device = device
        self._coordinator = coordinator
        self._battery_sensors: Dict[str, BatteryModuleSensor] = {}

    def process_quota_data(self, raw_params: Dict[str, Any]):
        _LOGGER.debug(f"BatterySensorManager.process_quota_data => got {len(raw_params)} keys")
        for key, val in raw_params.items():
            if not key.startswith("bp_addr."):
                continue
            if key in self._battery_sensors:
                continue

            _LOGGER.info(f"Discovered new Battery Module {key}")
            sensor_entity = BatteryModuleSensor(
                client=self._coordinator.client, 
                device=self._device, 
                battery_key=key, 
                name=f"Battery {key}"
            )
            self._battery_sensors[key] = sensor_entity
            self._add_entities([sensor_entity])

    def update_existing_sensors(self):
        for sensor in self._battery_sensors.values():
            sensor.update_from_coordinator()
