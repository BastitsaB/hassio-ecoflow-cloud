from custom_components.ecoflow_cloud.api import EcoflowApiClient
from custom_components.ecoflow_cloud.devices import const, BaseDevice
from custom_components.ecoflow_cloud.entities import (
    BaseSensorEntity, BaseNumberEntity, BaseSwitchEntity, BaseSelectEntity
)
from custom_components.ecoflow_cloud.number import ChargingPowerEntity, MaxBatteryLevelEntity, MinBatteryLevelEntity
from custom_components.ecoflow_cloud.select import DictSelectEntity, TimeoutDictSelectEntity
from custom_components.ecoflow_cloud.sensor import (
    LevelSensorEntity, WattsSensorEntity, TempSensorEntity, AmpSensorEntity, QuotaStatusSensorEntity
)
from custom_components.ecoflow_cloud.switch import EnabledEntity


class PowerOcean(BaseDevice):
    def sensors(self, client: EcoflowApiClient) -> list[BaseSensorEntity]:
        """Define sensors for the PowerOcean device."""
        return [
            # Battery and System Sensors
            LevelSensorEntity(client, self, "bpSoc", const.BATTERY_SOC),
            WattsSensorEntity(client, self, "bpPwr", const.BATTERY_POWER),
            LevelSensorEntity(client, self, "pcsAPhase.vol", const.PHASE_A_VOLTAGE),
            WattsSensorEntity(client, self, "pcsAPhase.actPwr", const.PHASE_A_ACTIVE_POWER),
            WattsSensorEntity(client, self, "pcsAPhase.reactPwr", const.PHASE_A_REACTIVE_POWER),
            AmpSensorEntity(client, self, "pcsAPhase.amp", const.PHASE_A_CURRENT),

            LevelSensorEntity(client, self, "pcsBPhase.vol", const.PHASE_B_VOLTAGE),
            WattsSensorEntity(client, self, "pcsBPhase.actPwr", const.PHASE_B_ACTIVE_POWER),
            WattsSensorEntity(client, self, "pcsBPhase.reactPwr", const.PHASE_B_REACTIVE_POWER),
            AmpSensorEntity(client, self, "pcsBPhase.amp", const.PHASE_B_CURRENT),

            LevelSensorEntity(client, self, "pcsCPhase.vol", const.PHASE_C_VOLTAGE),
            WattsSensorEntity(client, self, "pcsCPhase.actPwr", const.PHASE_C_ACTIVE_POWER),
            WattsSensorEntity(client, self, "pcsCPhase.reactPwr", const.PHASE_C_REACTIVE_POWER),
            AmpSensorEntity(client, self, "pcsCPhase.amp", const.PHASE_C_CURRENT),

            WattsSensorEntity(client, self, "sysLoadPwr", const.SYSTEM_LOAD_POWER),
            WattsSensorEntity(client, self, "sysGridPwr", const.GRID_POWER),

            # Solar and MPPT Sensors
            WattsSensorEntity(client, self, "mpptPwr", const.SOLAR_TOTAL_POWER),
            LevelSensorEntity(client, self, "mpptPv.vol", const.SOLAR_VOLTAGE),
            AmpSensorEntity(client, self, "mpptPv.amp", const.SOLAR_CURRENT),

            # Temperature Sensors
            TempSensorEntity(client, self, "sectorA.tempCurr", const.ZONE_A_TEMPERATURE),
            TempSensorEntity(client, self, "sectorB.tempCurr", const.ZONE_B_TEMPERATURE),
            TempSensorEntity(client, self, "hpMaster.tempInlet", const.INLET_TEMPERATURE),
            TempSensorEntity(client, self, "hpMaster.tempOutlet", const.OUTLET_TEMPERATURE),
            TempSensorEntity(client, self, "hpMaster.tempAmbient", const.AMBIENT_TEMPERATURE),

            # Quota Status
            QuotaStatusSensorEntity(client, self)
        ]

    def numbers(self, client: EcoflowApiClient) -> list[BaseNumberEntity]:
        """Define sliders (numbers) for PowerOcean."""
        return [
            MaxBatteryLevelEntity(client, self, "ems.maxChargeSoc", const.MAX_CHARGE_LEVEL, 50, 100,
                                  lambda value: {"moduleType": 0, "operateType": "TCP",
                                                 "params": {"id": 49, "maxChgSoc": value}}),
            MinBatteryLevelEntity(client, self, "ems.minDsgSoc", const.MIN_DISCHARGE_LEVEL, 0, 30,
                                  lambda value: {"moduleType": 0, "operateType": "TCP",
                                                 "params": {"id": 51, "minDsgSoc": value}}),
            ChargingPowerEntity(client, self, "inv.cfgSlowChgWatts", const.AC_CHARGING_POWER, 200, 2900,
                                lambda value: {"moduleType": 0, "operateType": "TCP",
                                               "params": {"slowChgPower": value, "id": 69}})
        ]

    def switches(self, client: EcoflowApiClient) -> list[BaseSwitchEntity]:
        """Define switches for PowerOcean."""
        return [
            EnabledEntity(client, self, "sysGridPwr.enabled", const.GRID_CONNECTION,
                          lambda value: {"moduleType": 0, "operateType": "TCP",
                                         "params": {"id": 72, "enabled": value}}),
            EnabledEntity(client, self, "sectorDhw.powerHeatEnabled", const.HEATING_ENABLED,
                          lambda value: {"moduleType": 0, "operateType": "TCP",
                                         "params": {"id": 91, "enabled": value}})
        ]

    def selects(self, client: EcoflowApiClient) -> list[BaseSelectEntity]:
        """Define select options for PowerOcean."""
        return [
            DictSelectEntity(client, self, "mppt.cfgDcChgCurrent", const.DC_CHARGE_CURRENT, const.DC_CHARGE_CURRENT_OPTIONS,
                             lambda value: {"moduleType": 0, "operateType": "TCP",
                                            "params": {"currMa": value, "id": 71}}),

            TimeoutDictSelectEntity(client, self, "pd.lcdOffSec", const.SCREEN_TIMEOUT, const.SCREEN_TIMEOUT_OPTIONS,
                                    lambda value: {"moduleType": 0, "operateType": "TCP",
                                                   "params": {"lcdTime": value, "id": 39}})
        ]
