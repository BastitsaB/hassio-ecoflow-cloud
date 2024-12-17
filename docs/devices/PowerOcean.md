## POWER_OCEAN

_Sensors_

- Phase A Voltage (`pcsAPhase.vol`)
- Phase A Current (`pcsAPhase.amp`)
- Phase A Active Power (`pcsAPhase.actPwr`)
- Phase A Reactive Power (`pcsAPhase.reactPwr`)
- Phase A Apparent Power (`pcsAPhase.apparentPwr`)
- Phase B Voltage (`pcsBPhase.vol`)
- Phase B Current (`pcsBPhase.amp`)
- Phase B Active Power (`pcsBPhase.actPwr`)
- Phase B Reactive Power (`pcsBPhase.reactPwr`)
- Phase B Apparent Power (`pcsBPhase.apparentPwr`)
- Phase C Voltage (`pcsCPhase.vol`)
- Phase C Current (`pcsCPhase.amp`)
- Phase C Active Power (`pcsCPhase.actPwr`)
- Phase C Reactive Power (`pcsCPhase.reactPwr`)
- Phase C Apparent Power (`pcsCPhase.apparentPwr`)
- Solar Total Power (`mpptPwr`)
- Solar Voltage (`mpptPv.vol`)
- Solar Current (`mpptPv.amp`)
- Battery SoC (`bpSoc`)
- Battery Power (`bpPwr`)
- System Load Power (`sysLoadPwr`)
- Grid Power (`sysGridPwr`)
- Zone A Temperature (`sectorA.tempCurr`)
- Zone B Temperature (`sectorB.tempCurr`)
- Inlet Temperature (`hpMaster.tempInlet`)
- Outlet Temperature (`hpMaster.tempOutlet`)
- Ambient Temperature (`hpMaster.tempAmbient`)
- Hot Water Temperature (`sectorDhw.tempCurr`)
- Error Codes (`emsErrCode.errCode`)
- Binary Error Code (`errorCode`)

_Switches_

- Grid Connection Enabled (`sysGridPwr.enabled` -> `{"moduleType": 0, "operateType": "TCP", "params": {"id": 72, "enabled": "VALUE"}}`)
- Heating Enabled (`sectorDhw.powerHeatEnabled` -> `{"moduleType": 0, "operateType": "TCP", "params": {"id": 91, "enabled": "VALUE"}}`)

_Sliders (numbers)_

- Max Charge Level (`ems.maxChargeSoc` -> `{"moduleType": 0, "operateType": "TCP", "params": {"id": 49, "maxChgSoc": "VALUE"}}` [50 - 100])
- Min Discharge Level (`ems.minDsgSoc` -> `{"moduleType": 0, "operateType": "TCP", "params": {"id": 51, "minDsgSoc": "VALUE"}}` [0 - 30])
- AC Charging Power (`inv.cfgSlowChgWatts` -> `{"moduleType": 0, "operateType": "TCP", "params": {"id": 69, "slowChgPower": "VALUE"}}` [200 - 2900])

_Selects_

- DC Charge Current (`mppt.cfgDcChgCurrent` -> `{"moduleType": 0, "operateType": "TCP", "params": {"currMa": "VALUE", "id": 71}}` [4A (4000), 6A (6000), 8A (8000)])
