import logging
from typing import Any, List, TypeVar

import jsonpath_ng.ext as jp
from homeassistant.util import utcnow, dt

_LOGGER = logging.getLogger(__name__)

_T = TypeVar("_T")
class BoundFifoList(List):

    def __init__(self, maxlen=20) -> None:
        super().__init__()
        self.maxlen = maxlen

    def append(self, __object: _T) -> None:
        super().insert(0, __object)
        while len(self) >= self.maxlen:
            self.pop()



class EcoflowDataHolder:

    def __init__(self, collect_raw: bool = False):
        self.__collect_raw = collect_raw
        self.set = BoundFifoList[dict[str, Any]]()
        self.set_reply = BoundFifoList[dict[str, Any]]()
        self.set_reply_time = dt.utcnow().replace(year=2000, month=1, day=1, hour=0, minute=0, second=0)

        self.get = BoundFifoList[dict[str, Any]]()
        self.get_reply = BoundFifoList[dict[str, Any]]()
        self.get_reply_time = dt.utcnow().replace(year=2000, month=1, day=1, hour=0, minute=0, second=0)

        self.params = dict[str, Any]()
        self.params_time = dt.utcnow().replace(year=2000, month=1, day=1, hour=0, minute=0, second=0)

        self.status = dict[str, Any]()
        self.status_time = dt.utcnow().replace(year=2000, month=1, day=1, hour=0, minute=0, second=0)

        self.raw_data = BoundFifoList[dict[str, Any]]()

    def last_received_time(self):
        return max(self.status_time, self.params_time, self.get_reply_time, self.set_reply_time)

    def add_set_message(self, msg: dict[str, Any]):
        self.set.append(msg)

    def add_set_reply_message(self, msg: dict[str, Any]):
        self.set_reply.append(msg)
        self.set_reply_time = dt.utcnow()

    def add_get_message(self, msg: dict[str, Any]):
        self.get.append(msg)

    def add_get_reply_message(self, msg: dict[str, Any]):

        if "operateType" in msg and msg["operateType"] == "latestQuotas":
            online = int(msg["data"]["online"])
            if online == 1:
                self.update_data({"params": msg["data"]["quotaMap"], "time": utcnow()})

        self.get_reply.append(msg)
        self.get_reply_time = dt.utcnow()


    def update_to_target_state(self, target_state: dict[str, Any]):
        # key can be xpath!
        for key, value in target_state.items():
            jp.parse(key).update(self.params, value)

        self.params_time = dt.utcnow()

    def update_status(self, raw: dict[str, Any]):
        self.status.update({"status" : int(raw['params']['status'])})
        self.status_time = dt.utcnow()

    def update_data(self, raw: dict[str, Any]):
        self.__add_raw_data(raw)
        try:
            self.params.update(raw['params'])
            self.params_time = dt.utcnow()

        except Exception as error:
            _LOGGER.error("Error updating data: %s", error)

    def __add_raw_data(self, raw: dict[str, Any]):
        if self.__collect_raw:
            self.raw_data.append(raw)
