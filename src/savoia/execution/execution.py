from abc import ABCMeta, abstractmethod
from savoia.event.event import OrderEvent, FillEvent, Event
from savoia.config.decimal_config import DECIMAL_PLACES

import pandas as pd
from queue import Queue, Empty
from decimal import Decimal
from logging import getLogger, Logger
import time


class ExecutionHandler(metaclass=ABCMeta):
    """
    Provides an abstract base class to handle all execution in the
    backtesting and live trading system.
    """
    @abstractmethod
    def __init__(self, event_q: 'Queue[Event]', exec_q: 'Queue[Event]',
            heartbeat: float = 3):
        pass

    @abstractmethod
    def run(self) -> None:
        pass


class SimulatedExecution(ExecutionHandler):
    logger: Logger
    event_q: 'Queue[Event]'
    exec_q: 'Queue[Event]'

    def __init__(self, event_q: 'Queue[Event]', exec_q: 'Queue[Event]',
            heartbeat: float = 0) -> None:
        self.logger = getLogger(__name__)
        self.exec_q = exec_q
        self.event_q = event_q
        self.heartbeat = heartbeat

    def _execute_order(self, event: OrderEvent) -> None:
        import random
        ref = event.ref
        instrument = event.instrument
        units = event.units
        price = event.price * Decimal(str(random.uniform(0.99, 1.01)))
        price = price.quantize(DECIMAL_PLACES)
        status = 'filled'
        dt = event.time + pd.offsets.Second(random.randint(3, 10))
        fillevent = FillEvent(ref, instrument, units, price, status, dt)
        self._return_fill_event(fillevent)

    def _return_fill_event(self, event: FillEvent) -> None:
        self.event_q.put(event)
    
    def run(self) -> None:
        while True:
            try:
                _event = self.exec_q.get(False)
            except Empty:
                pass
            else:
                if _event is None:
                    break
                else:
                    self._execute_order(_event)
            time.sleep(self.heartbeat)


# class OANDAExecutionHandler(ExecutionHandler):
#     def __init__(self, domain, access_token, account_id):
#         self.domain = domain
#         self.access_token = access_token
#         self.account_id = account_id
#         self.conn = self.obtain_connection()
#         self.logger = logging.getLogger(__name__)

#     def obtain_connection(self):
#         return httplib.HTTPSConnection(self.domain)

#     def execute_order(self, event):
#         instrument = "%s_%s" % (event.instrument[:3], event.instrument[3:])
#         headers = {
#             "Content-Type": "application/x-www-form-urlencoded",
#             "Authorization": "Bearer " + self.access_token
#         }
#         params = urlencode({
#             "instrument": instrument,
#             "units": event.units,
#             "type": event.order_type,
#             "side": event.side
#         })
#         self.conn.request(
#             "POST",
#             "/v1/accounts/%s/orders" % str(self.account_id),
#             params, headers
#         )
#         response = self.conn.getresponse().read()\
#             .decode("utf-8").replace("\n", "").replace("\t", "")

#         self.logger.debug(response)
