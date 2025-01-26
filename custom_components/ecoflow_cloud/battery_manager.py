from __future__ import annotations

import logging
import json

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

class BatterySensorManager:
    """
    Verwalte dynamisch Sensoren pro Battery-SN (z.B. bp_addr.HJ32ZDH4XYZ...).
    """

    def __init__(self, add_entities_callback: AddEntitiesCallback, device, coordinator):
        self._add_entities = add_entities_callback
        self._device = device
        self._coordinator = coordinator

        # Merkt sich, welche Batterien schon angelegt sind
        self._battery_sensors: dict[str, BatteryModuleSensor] = {}

    def process_quota_data(self, raw_params: dict[str, any]):
        _LOGGER.debug(f"BatterySensorManager.process_quota_data => got {len(raw_params)} keys")
        _LOGGER.debug("process_quota_data => found %s keys in raw_params", len(raw_params))
        """
        Wird nach jedem Coordinator-Update aufgerufen,
        um in raw_params nach 'bp_addr.<SN>'-Feldern zu suchen und ggf. neue Entities anzulegen.
        """
        for key, val in raw_params.items():
            if not key.startswith("bp_addr."):
                _LOGGER.debug(f"BatterySensorManager sees battery key = {key}")
                continue
            # key z.B. "bp_addr.HJ32ZDH4ZF7E0051"
            # val z.B. ein JSON-String => {"bpSoc":17,"bpSoh":99,...}
            if key in self._battery_sensors:
                # Schon angelegt => nur updaten
                continue

            # Neues Battery-SN-Entity anlegen
            _LOGGER.info(f"Discovered new Battery Module {key}")
            sensor_entity = BatteryModuleSensor(self._device, self._coordinator, key)
            self._battery_sensors[key] = sensor_entity

            # Jetzt im HA-System registrieren
            self._add_entities([sensor_entity])

    def update_existing_sensors(self):
        """
        Coordinator hat neue Daten => existierende Entities aktualisieren
        (In HA macht das normal 'CoordinatorEntity' auto. 
         Hier aber kann man manuell .schedule_update_ha_state() aufrufen, wenn nötig.)
        """
        for sensor in self._battery_sensors.values():
            sensor.update_from_coordinator()

class BatteryModuleSensor(Entity):
    """
    Repräsentiert EINE Batteriemodul-Einheit. Holt Daten aus bp_addr.<SN>.
    Zeigt z.B. bpSoc, bpSoh, bpTemp etc. als Attribute an oder man baut
    pro Info einen Sub-Sensor => Variation.
    """

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
        """Alle relevanten Felder aus coordinator.data (params) auslesen und in self._attrs speichern."""
        params = self._device.data.params
        # params["bp_addr.HJ32ZDH4ZF7E0051.bpSoc"], z.B.

        # z.B. "bp_addr.HJ32ZDH4ZF7E0051.bpSoc" => Key = f"{self._battery_key}.bpSoc"
        # Sammeln wir mal State = SoC
        main_soc_key = f"{self._battery_key}.bpSoc"
        if main_soc_key in params:
            self._state = params[main_soc_key]
        else:
            self._state = "unknown"

        # z.B. S0H, cycles etc. => als Attribute
        soh_key = f"{self._battery_key}.bpSoh"
        cyc_key = f"{self._battery_key}.bpCycles"
        if soh_key in params:
            self._attrs["bpSoh"] = params[soh_key]
        if cyc_key in params:
            self._attrs["bpCycles"] = params[cyc_key]

        # Weitere Felder (Temperaturen, Akkuleistung etc.) 
        # -> in self._attrs
        # z.B. "bp_addr.HJ32ZDH4ZF7E0051.bpTemp" => array
        temp_key = f"{self._battery_key}.bpTemp"
        if temp_key in params:
            self._attrs["bpTemp"] = params[temp_key]

        # ... etc. so viele Felder du willst ...
        self.schedule_update_ha_state()

    def update(self):
        """
        Standard-HA-Funktion: 
        Ruft update_from_coordinator auf (im Sync-Context).
        """
        self.update_from_coordinator()
