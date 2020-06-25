from abc import ABCMeta, abstractmethod
from savoia.event.event import OrderEvent


class ExecutionHandler(metaclass=ABCMeta):
    """
    Provides an abstract base class to handle all execution in the
    backtesting and live trading system.
    """

    @abstractmethod
    def execute_order(self, event: OrderEvent) -> None:
        """
        Send the order to the brokerage.
        """
        pass


class SimulatedExecution(ExecutionHandler):
    def execute_order(self, event: OrderEvent) -> None:
        pass


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
