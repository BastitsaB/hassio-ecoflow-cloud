# ecoflow_cloud/sensor.py

import logging
import struct
from typing import Any, Mapping, OrderedDict, Dict

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.components.sensor import (SensorDeviceClass, SensorStateClass, SensorEntity)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (PERCENTAGE,
                                 UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfEnergy, UnitOfFrequency,
                                 UnitOfPower, UnitOfTemperature, UnitOfTime)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt

from . import ECOFLOW_DOMAIN, ATTR_STATUS_SN, ATTR_STATUS_DATA_LAST_UPDATE, ATTR_STATUS_LAST_UPDATE, \
    ATTR_STATUS_RECONNECTS, \
    ATTR_STATUS_PHASE, ATTR_MQTT_CONNECTED, ATTR_QUOTA_REQUESTS
from .api import EcoflowApiClient
from .entities import BaseSensorEntity, EcoFlowAbstractEntity, EcoFlowDictEntity
from .battery_manager import BatterySensorManager
from .devices import BaseDevice, EcoflowDeviceUpdateCoordinator, DeviceData  # Korrekte Importe

_LOGGER = logging.getLogger(__name__)  # Initialisierung des Loggers

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client: EcoflowApiClient = hass.data[ECOFLOW_DOMAIN][entry.entry_id]

    for sn, device in client.devices.items():
        # Konfiguriere das Gerät, falls noch nicht geschehen
        if device.coordinator is None:
            device.configure(
                hass=hass,
                refresh_period=60,  # Beispielintervall, passe es nach Bedarf an
                diag=True,
                client=client
            )

        # Hinzufügen statischer Sensoren
        static_sensors = device.sensors(client)
        async_add_entities(static_sensors)

        # Initialisierung des BatterySensorManagers
        manager = BatterySensorManager(
            add_entities_callback=async_add_entities, 
            device=device, 
            coordinator=device.coordinator
        )

        # Listener registrieren
        def after_update():
            _LOGGER.debug("after_update triggered for device: %s", device.device_info.sn)
            params = device.data.params
            _LOGGER.debug("Device params: %s", params)
            manager.process_quota_data(params)
            manager.update_existing_sensors()

        device.coordinator.async_add_listener(after_update)
        # Starte den Coordinator, falls noch nicht gestartet
        if not device.coordinator.async_is_running():
            await device.coordinator.async_refresh()

# Beispielhafte Sensor-Entity-Klassen bleiben unverändert

class MiscBinarySensorEntity(BinarySensorEntity, EcoFlowDictEntity):
    """Ein Beispiel für eine BinarySensor-Entity."""

    def _update_value(self, val: Any) -> bool:
        self._attr_is_on = bool(val)
        return True

class ChargingStateSensorEntity(BaseSensorEntity):
    """Sensor-Entity für den Ladezustand der Batterie."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:battery-charging"
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def _update_value(self, val: Any) -> bool:
        if val == 0:
            return super()._update_value("unused")
        elif val == 1:
            return super()._update_value("charging")
        elif val == 2:
            return super()._update_value("discharging")
        else:
            return False

class CyclesSensorEntity(BaseSensorEntity):
    """Sensor-Entity für die Anzahl der Batteriezyklen."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:battery-heart-variant"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

class FanSensorEntity(BaseSensorEntity):
    """Sensor-Entity für den Lüfterstatus."""
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:fan"

class MiscSensorEntity(BaseSensorEntity):
    """Ein allgemeiner Sensor für verschiedene Daten."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC

class LevelSensorEntity(BaseSensorEntity):
    """Sensor-Entity für den Ladezustand der Batterie (bpSoc)."""
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

class RemainSensorEntity(BaseSensorEntity):
    """Sensor-Entity für verbleibende Zeit."""
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_value = 0

    def _update_value(self, val: Any) -> Any:
        ival = int(val)
        if ival < 0 or ival > 5000:
            ival = 0
        return super()._update_value(ival)

class SecondsRemainSensorEntity(BaseSensorEntity):
    """Sensor-Entity für verbleibende Sekunden."""
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_value = 0

    def _update_value(self, val: Any) -> Any:
        ival = int(val)
        if ival < 0 or ival > 5000:
            ival = 0
        return super()._update_value(ival)

class TempSensorEntity(BaseSensorEntity):
    """Sensor-Entity für die Batterietemperatur."""
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_value = -1

class CelsiusSensorEntity(TempSensorEntity):
    def _update_value(self, val: Any) -> bool:
        return super()._update_value(int(val))

class DecicelsiusSensorEntity(TempSensorEntity):
    def _update_value(self, val: Any) -> bool:
        return super()._update_value(int(val) / 10)

class MilliCelsiusSensorEntity(TempSensorEntity):
    def _update_value(self, val: Any) -> bool:
        return super()._update_value(int(val) / 100)

class VoltSensorEntity(BaseSensorEntity):
    """Sensor-Entity für Spannung."""
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_value = 0

class MilliVoltSensorEntity(BaseSensorEntity):
    """Sensor-Entity für Millivolt."""
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfElectricPotential.MILLIVOLT
    _attr_suggested_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_value = 3

class BeSensorEntity(BaseSensorEntity):
    """Beispiel Sensor-Entity für spezielle Berechnungen."""
    def _update_value(self, val: Any) -> bool:
        return super()._update_value(int(struct.unpack('<I', struct.pack('>I', val))[0]))

class BeMilliVoltSensorEntity(BeSensorEntity):
    """Spezialisierte Millivolt Sensor-Entity."""
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfElectricPotential.MILLIVOLT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_value = 0

class InMilliVoltSensorEntity(MilliVoltSensorEntity):
    """Sensor-Entity für eingehende Millivolt."""
    _attr_icon = "mdi:transmission-tower-import"
    _attr_suggested_display_precision = 0

class OutMilliVoltSensorEntity(MilliVoltSensorEntity):
    """Sensor-Entity für ausgehende Millivolt."""
    _attr_icon = "mdi:transmission-tower-export"
    _attr_suggested_display_precision = 0

class DecivoltSensorEntity(BaseSensorEntity):
    """Sensor-Entity für Dezivolt."""
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_value = 0

    def _update_value(self, val: Any) -> bool:
        return super()._update_value(int(val) / 10)

class CentivoltSensorEntity(DecivoltSensorEntity):
    """Sensor-Entity für Centivolt."""
    def _update_value(self, val: Any) -> bool:
        return super()._update_value(int(val) / 10)

class AmpSensorEntity(BaseSensorEntity):
    """Sensor-Entity für Stromstärke."""
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.MILLIAMPERE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_value = 0

class DeciampSensorEntity(BaseSensorEntity):
    """Sensor-Entity für Deziamper."""
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_value = 0

    def _update_value(self, val: Any) -> bool:
        return super()._update_value(int(val) / 10)

class WattsSensorEntity(BaseSensorEntity):
    """Sensor-Entity für Leistung in Watt."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_value = 0

class EnergySensorEntity(BaseSensorEntity):
    """Sensor-Entity für Energie in Wattstunden."""
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def _update_value(self, val: Any) -> bool:
        ival = int(val)
        if ival > 0:
            return super()._update_value(ival)
        else:
            return False

class CapacitySensorEntity(BaseSensorEntity):
    """Sensor-Entity für Kapazität in mAh."""
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = "mAh"
    _attr_state_class = SensorStateClass.MEASUREMENT

class DeciwattsSensorEntity(WattsSensorEntity):
    """Sensor-Entity für Dezileistung."""
    def _update_value(self, val: Any) -> bool:
        return super()._update_value(int(val) / 10)

class InWattsSensorEntity(WattsSensorEntity):
    """Sensor-Entity für eingehende Leistung."""
    _attr_icon = "mdi:transmission-tower-import"

class InWattsSolarSensorEntity(InWattsSensorEntity):
    """Sensor-Entity für eingehende Solarbeiträge."""
    _attr_icon = "mdi:solar-power"

    def _update_value(self, val: Any) -> bool:
        return super()._update_value(int(val) / 10)

class OutWattsSensorEntity(WattsSensorEntity):
    """Sensor-Entity für ausgehende Leistung."""
    _attr_icon = "mdi:transmission-tower-export"

class OutWattsDcSensorEntity(WattsSensorEntity):
    """Sensor-Entity für ausgehende DC-Leistung."""
    _attr_icon = "mdi:transmission-tower-export"

    def _update_value(self, val: Any) -> bool:
        return super()._update_value(int(val) / 10)

class InVoltSensorEntity(VoltSensorEntity):
    """Sensor-Entity für eingehende Spannung."""
    _attr_icon = "mdi:transmission-tower-import"

class InVoltSolarSensorEntity(VoltSensorEntity):
    """Sensor-Entity für eingehende Solarpotential."""
    _attr_icon = "mdi:solar-power"

    def _update_value(self, val: Any) -> bool:
        return super()._update_value(int(val) / 10)

class OutVoltDcSensorEntity(VoltSensorEntity):
    """Sensor-Entity für ausgehende DC-Spannung."""
    _attr_icon = "mdi:transmission-tower-export"
        
    def _update_value(self, val: Any) -> bool:
        return super()._update_value(int(val) / 10)      

class InAmpSensorEntity(AmpSensorEntity):
    """Sensor-Entity für eingehende Stromstärke."""
    _attr_icon = "mdi:transmission-tower-import"

class InAmpSolarSensorEntity(AmpSensorEntity):
    """Sensor-Entity für eingehende Solarmaß."""
    _attr_icon = "mdi:solar-power"

    def _update_value(self, val: Any) -> bool:
        return super()._update_value(int(val) * 10)

class InEnergySensorEntity(EnergySensorEntity):
    """Sensor-Entity für eingehende Energie."""
    _attr_icon = "mdi:transmission-tower-import"

class OutEnergySensorEntity(EnergySensorEntity):
    """Sensor-Entity für ausgehende Energie."""
    _attr_icon = "mdi:transmission-tower-export"

class FrequencySensorEntity(BaseSensorEntity):
    """Sensor-Entity für Frequenz."""
    _attr_device_class = SensorDeviceClass.FREQUENCY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = UnitOfFrequency.HERTZ
    _attr_state_class = SensorStateClass.MEASUREMENT

class DecihertzSensorEntity(FrequencySensorEntity):
    """Sensor-Entity für Dezihertz."""
    def _update_value(self, val: Any) -> bool:
        return super()._update_value(int(val) / 10)

class StatusSensorEntity(SensorEntity, EcoFlowAbstractEntity):
    """Sensor-Entity für den Status der Verbindung."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, client: EcoflowApiClient, device: BaseDevice):
        super().__init__(client, device, "Status", "status")
        self._online = -1
        self._last_update = dt.utcnow().replace(year=2000, month=1, day=1, hour=0, minute=0, second=0)
        self._skip_count = 0
        self._offline_skip_count = int(120 / self.coordinator.update_interval.seconds) # 2 minutes
        self._attrs = OrderedDict[str, Any]()
        self._attrs[ATTR_STATUS_SN] = self._device.device_info.sn
        self._attrs[ATTR_STATUS_DATA_LAST_UPDATE] = None
        self._attrs[ATTR_MQTT_CONNECTED] = None

    def _handle_coordinator_update(self) -> None:
        """Verarbeitet Updates vom Coordinator."""
        changed = False
        update_time = self.coordinator.data.data_holder.last_received_time()
        if self._last_update < update_time:
            self._last_update = max(update_time, self._last_update)
            self._attrs[ATTR_STATUS_DATA_LAST_UPDATE] = update_time
            self._attrs[ATTR_MQTT_CONNECTED] = self._client.mqtt_client.is_connected()
            self._skip_count = 0
            changed = True
        else:
            self._skip_count += 1

        changed = self._actualize_status() or changed

        if changed:
            self.schedule_update_ha_state()

    def _actualize_status(self) -> bool:
        """Aktualisiert den Status basierend auf dem Skip-Count."""
        changed = False
        if self._online != 0 and self._skip_count >= self._offline_skip_count:
            self._online = 0
            self._attr_native_value = "assume_offline"
            self._attrs[ATTR_MQTT_CONNECTED] = self._client.mqtt_client.is_connected()
            changed = True
        elif self._online != 1 and self._skip_count == 0:
            self._online = 1
            self._attr_native_value = "online"
            self._attrs[ATTR_MQTT_CONNECTED] = self._client.mqtt_client.is_connected()
            changed = True
        return changed

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        return self._attrs

class QuotaStatusSensorEntity(StatusSensorEntity):
    """Sensor-Entity für den Quota-Status."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, client: EcoflowApiClient, device: BaseDevice):
        super().__init__(client, device)
        self._attrs[ATTR_QUOTA_REQUESTS] = 0

    def _actualize_status(self) -> bool:
        """Aktualisiert den Quota-Status."""
        changed = False
        if self._online != 0 and self._skip_count >= self._offline_skip_count * 2:
            self._online = 0
            self._attr_native_value = "assume_offline"
            self._attrs[ATTR_MQTT_CONNECTED] = self._client.mqtt_client.is_connected()
            changed = True
        elif self._online != 0 and self._skip_count >= self._offline_skip_count:
            self.hass.async_create_background_task(self._client.quota_all(self._device.device_info.sn), "get quota")
            self._attrs[ATTR_QUOTA_REQUESTS] = self._attrs[ATTR_QUOTA_REQUESTS] + 1
            changed = True
        elif self._online != 1 and self._skip_count == 0:
            self._online = 1
            self._attr_native_value = "online"
            self._attrs[ATTR_MQTT_CONNECTED] = self._client.mqtt_client.is_connected()
            changed = True
        return changed

class ReconnectStatusSensorEntity(StatusSensorEntity):
    """Sensor-Entity für den Reconnect-Status."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    CONNECT_PHASES = [3, 5, 7]

    def __init__(self, client: EcoflowApiClient, device: BaseDevice):
        super().__init__(client, device)
        self._attrs[ATTR_STATUS_PHASE] = 0
        self._attrs[ATTR_STATUS_RECONNECTS] = 0

    def _actualize_status(self) -> bool:
        """Aktualisiert den Reconnect-Status."""
        time_to_reconnect = self._skip_count in self.CONNECT_PHASES

        if self._online == 1 and time_to_reconnect:
            self._attrs[ATTR_STATUS_RECONNECTS] = self._attrs[ATTR_STATUS_RECONNECTS] + 1
            self._client.mqtt_client.reconnect()
            return True
        else:
            return super()._actualize_status()

# Restliche Sensor-Entities bleiben unverändert

class SolarPowerSensorEntity(WattsSensorEntity):
    """Sensor-Entity für Solarpower."""
    _attr_entity_category = None
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:solar-power"

class SolarAmpSensorEntity(AmpSensorEntity):
    """Sensor-Entity für Solarmaß."""
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:current-dc"

class SystemPowerSensorEntity(WattsSensorEntity):
    """Sensor-Entity für Systemleistung."""
    _attr_entity_category = None
    _attr_suggested_display_precision = 1

    def __init__(self, client: EcoflowApiClient, device: BaseDevice, key: str, name: str):
        super().__init__(client, device, key, name)
        self.key = key  # z.B. "sysGridPwr" oder "sysLoadPwr"

    def update_from_coordinator(self):
        """Liest die Daten aus dem Coordinator und aktualisiert den Sensor."""
        params = self._device.data.params
        value = params.get(self.mqtt_key, "unknown")
        if isinstance(value, (int, float, list)):
            _LOGGER.debug(f"{self.name} ({self.mqtt_key}) updated with value: {value}")
            if self._update_value(value):
                self.schedule_update_ha_state()
        else:
            _LOGGER.warning(f"Invalid value for {self.name} ({self.mqtt_key}): {value}")
            self._update_value("unknown")
            self.schedule_update_ha_state()

    def update(self):
        """Triggern der Aktualisierung."""
        self.update_from_coordinator()

class ErrorListSensorEntity(BaseSensorEntity):
    """Sensor-Entity für eine Liste von Fehlern."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:alert-circle-outline"
    _attr_native_value = None

    def _update_value(self, val: Any) -> bool:
        # val sollte ein Array / Liste mit Errorcodes sein
        if isinstance(val, list):
            if len(val) == 0:
                return super()._update_value("No errors")
            # Ansonsten Komma-separieren
            s = ",".join(str(x) for x in val)
            return super()._update_value(s)
        elif val is None:
            return super()._update_value("No data")
        else:
            # Falls es ein einzelner Fehlercode ist
            return super()._update_value(str(val))
        
class BatteryModuleSensor(BaseSensorEntity):
    """Sensor-Entity für ein einzelnes Batteriemodul."""

    def __init__(self, client: EcoflowApiClient, device: BaseDevice, battery_key: str, name: str):
        super().__init__(client, device, battery_key, name)
        self.mqtt_key = battery_key  # z.B. "bp_addr.HJ32ZDH4ZF7E0051.bpSoc"

    @property
    def native_unit_of_measurement(self) -> str:
        if self.mqtt_key.endswith("bpSoc"):
            return PERCENTAGE
        elif self.mqtt_key.endswith("bpCycles"):
            return "cycles"
        elif self.mqtt_key.endswith("bpAccuChgEnergy") or self.mqtt_key.endswith("bpAccuDsgEnergy"):
            return UnitOfEnergy.WATT_HOUR
        elif self.mqtt_key.endswith("bpTemp"):
            return UnitOfTemperature.CELSIUS
        else:
            return None

    @property
    def device_class(self) -> str:
        if self.mqtt_key.endswith("bpSoc"):
            return SensorDeviceClass.BATTERY
        elif self.mqtt_key.endswith("bpCycles"):
            return None  # Kein spezifischer Device-Class
        elif self.mqtt_key.endswith("bpAccuChgEnergy") or self.mqtt_key.endswith("bpAccuDsgEnergy"):
            return SensorDeviceClass.ENERGY
        elif self.mqtt_key.endswith("bpTemp"):
            return SensorDeviceClass.TEMPERATURE
        else:
            return None

    @property
    def state_class(self) -> str:
        if self.mqtt_key.endswith("bpAccuChgEnergy") or self.mqtt_key.endswith("bpAccuDsgEnergy"):
            return SensorStateClass.TOTAL_INCREASING
        else:
            return SensorStateClass.MEASUREMENT
