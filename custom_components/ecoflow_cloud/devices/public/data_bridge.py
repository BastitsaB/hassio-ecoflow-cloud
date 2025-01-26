
plain_to_status: dict[str, str] = {
        "pd": "pdStatus",
        "mppt": "mpptStatus",
        "bms_emsStatus": "emsStatus",
        "bms_bmsStatus": "bmsStatus",
        "inv": "invStatus",
        "bms_slave": "bmsSlaveStatus",
        "bms_slave_bmsSlaveStatus_1": "bmsSlaveStatus_1",
        "bms_slave_bmsSlaveStatus_2": "bmsSlaveStatus_2"
}

status_to_plain = dict((v, k) for (k, v) in plain_to_status.items())

def to_plain(raw_data: dict[str, any]) -> dict[str, any]:
    if "typeCode" in raw_data:
        prefix = status_to_plain.get(raw_data["typeCode"], "unknown_"+raw_data["typeCode"])
        new_params = {}
        if "params" in raw_data:
            for (k, v) in raw_data["params"].items():
                new_params[f"{prefix}.{k}"] = v
        if "param" in raw_data:
            for (k, v) in raw_data["param"].items():
                new_params[f"{prefix}.{k}"] = v

        result = {"params": new_params}
        for (k, v) in raw_data.items():
            if k != "param" and k != "params":
                result[k] = v

        return result
    else:
        if "cmdFunc" in raw_data and "cmdId" in raw_data:
            new_params = {}
            prefix = f"{raw_data['cmdFunc']}_{raw_data['cmdId']}"

            if "param" in raw_data:
                for (k, v) in raw_data["param"].items():
                    new_params[f"{prefix}.{k}"] = v

            if "params" in raw_data:
                for (k, v) in raw_data["params"].items():
                    new_params[f"{prefix}.{k}"] = v

            result = {"params": new_params}
            for (k, v) in raw_data.items():
                if k != "param" and k != "params":
                    result[k] = v

            return result

        return raw_data
    
def to_plain_other(raw_data: dict[str, any]) -> dict[str, any]:
    
    # 1) Prüfen, ob "code","message","data" => Quota-All JSON
    if "code" in raw_data and "message" in raw_data and "data" in raw_data:
        new_params = {}

        # Kopiere alles aus raw_data["data"] nach new_params
        data_dict = raw_data["data"]
        for k, v in data_dict.items():
            new_params[k] = v

        # Optional: bp_addr.* Einträge entpacken
        # (z. B. "bp_addr.HJ32ZDH4ZF7E0051" enthält JSON als String)
        for key in list(new_params.keys()):
            if key.startswith("bp_addr.") and isinstance(new_params[key], str):
                try:
                    sub_json = json.loads(new_params[key])
                    for sub_k, sub_val in sub_json.items():
                        new_params[f"{key}.{sub_k}"] = sub_val
                except Exception as exc:
                    _LOGGER.debug(
                        f"Unable to parse JSON in {key}: {new_params[key]} => {exc}"
                    )

        # Baue ein "params"-Dict
        result = {"params": new_params}
        # Kopiere restliche Felder ("code","message", etc.), ABER nicht "data"
        for (k, v) in raw_data.items():
            if k != "data":
                result[k] = v

        return result

    # 2) Falls cmdFunc/cmdId (alte Logik)
    if "cmdFunc" in raw_data and "cmdId" in raw_data:
        new_params = {}

        if "param" in raw_data:
            # Falls "addr" == "ems" und "cmdId" == 1 => Reine Phase-Extraktion
            if raw_data.get("addr") == "ems" and raw_data["cmdId"] == 1:
                phases = ["pcsAPhase", "pcsBPhase", "pcsCPhase"]
                for i, phase in enumerate(phases):
                    if phase in raw_data["param"]:
                        for k, v in raw_data["param"][phase].items():
                            new_params[f"{phase}.{k}"] = v

                if "mpptHeartBeat" in raw_data["param"]:
                    mpptHB = raw_data["param"]["mpptHeartBeat"]
                    if isinstance(mpptHB, list) and len(mpptHB) > 0:
                        mpptPvList = mpptHB[0].get("mpptPv", [])
                        for i, mpptpv_vals in enumerate(mpptPvList):
                            mpptpv_name = f"mpptPv{i+1}"
                            for k, v in mpptpv_vals.items():
                                new_params[f"{mpptpv_name}.{k}"] = v
            else:
                # Generisches Kopieren
                for (k, v) in raw_data["param"].items():
                    new_params[k] = v

        # Falls "params" extra existiert
        if "params" in raw_data:
            for (k, v) in raw_data["params"].items():
                new_params[k] = v

        result = {"params": new_params}
        for (k, v) in raw_data.items():
            if k not in ("param", "params"):
                result[k] = v

        return result

    # 3) Falls nix passt, Rückgabe unverändert
    return raw_data
