from abc import ABCMeta, abstractmethod
from savoia.event.event import OrderEvent, FillEvent, Event
from savoia.types.types import Pair

from queue import Queue
from decimal import Decimal


class ExecutionHandler(metaclass=ABCMeta):
    """
    Provides an abstract base class to handle all execution in the
    backtesting and live trading system.
    """
    @abstractmethod
    def __init__(self, events_queue: 'Queue[Event]'):
        pass

    @abstractmethod
    def execute_order(self, event: OrderEvent) -> None:
        """
        Send the order to the brokerage.
        """
        pass

    @abstractmethod
    def _return_fill_event(self, pair: Pair, units: Decimal, price: Decimal,
            side: str, status: str) -> None:
        """Return a Fill event"""
        pass


class SimulatedExecution(ExecutionHandler):
    events_queue: 'Queue[Event]'

    def __init__(self, events_queue: 'Queue[Event]') -> None:
        self.events_queue = events_queue

    def execute_order(self, event: OrderEvent) -> None:
        import random
        self._return_fill_event(event.instrument, event.units,
            Decimal(str(random.uniform(0.9889, 1.1212))), event.side, 'filled')

    def _return_fill_event(self, pair: Pair, units: Decimal, price: Decimal,
            side: str, status: str) -> None:
        self.events_queue.put(FillEvent(pair, units, price, side, status))


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
