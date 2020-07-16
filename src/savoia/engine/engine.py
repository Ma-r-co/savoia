from savoia.types.types import Pair
from savoia.event.event import Event
from savoia.datafeed.datafeed import DataFeeder
from savoia.ticker.ticker import Ticker
from savoia.strategy.strategy import Strategy
from savoia.portfolio.portfolio import Portfolio
from savoia.execution.execution import ExecutionHandler
from savoia.result.result import Result, ResultHandler
from savoia.config.decimal_config import initializeDecimalContext

from logging import getLogger, Logger
from typing import List, Dict, Union
from typing_extensions import TypedDict
from decimal import Decimal
from importlib import import_module
from queue import Queue, Empty
import time
import threading


class datafeed_params(TypedDict):
    module_name: str
    params: Dict[str, Union[str, Decimal, int, float, List[Pair],
        'Queue[Event]']]


class execution_params(TypedDict):
    module_name: str
    params: Dict[str, Union[str, Decimal, int, float, 'Queue[Event]']]


class strategy_params(TypedDict):
    module_name: str
    params: Dict[str, Union[str, Decimal, int, float, List[Pair],
        'Queue[Event]']]


class result_params(TypedDict):
    module_name: str
    params: Dict[str, Union[str, Decimal, int, float, List[Pair],
        'Queue[Result]']]


class engine_params(TypedDict):
    pairs: List[Pair]
    home_currency: str
    equity: Decimal
    isBacktest: bool
    max_iters: int
    heart_beat: float


class Engine(object):
    """
    Enscapsulates the settings and components for carrying out
    an event-driven trading/backtest on the foreign exchange markets.
    """
    logger: Logger
    pairs: List[Pair]
    datafeed: DataFeeder
    execution: ExecutionHandler
    strategy: Strategy
    result: ResultHandler
    portfolio: Portfolio
    ticker: Ticker
    equity: Decimal
    home_currency: str
    heartbeat: float
    max_iters: int
    iters: int
    event_q: 'Queue[Event]'
    feed_q: 'Queue[Event]'
    exec_q: 'Queue[Event]'
    result_q: 'Queue[Result]'

    def __init__(
        self, engine: engine_params, datafeed: datafeed_params,
        execution: execution_params, strategy: strategy_params,
        result: result_params
    ):
        """
        Initializes the backtest.
        """
        self.logger = getLogger(__name__)
        self.pairs = engine['pairs']
        self.home_currency = engine['home_currency']
        self.equity = engine['equity']
        self.isBacktest = engine['isBacktest']
        self.max_iters = engine['max_iters']
        self.heartbeat = engine['heart_beat']
        self.event_q = Queue()
        self.feed_q = Queue()
        self.exec_q = Queue()
        self.result_q = Queue()
        self.iters = 0
        self.datafeed = self._setup_datafeed(datafeed)
        self.execution = self._setup_execution(execution)
        self.strategy = self._setup_strategy(strategy)
        self.result = self._setup_result(result)
        self.ticker = Ticker(self.pairs)
        self.portfolio = Portfolio(
            ticker=self.ticker,
            event_q=self.event_q,
            result_q=self.result_q,
            home_currency=self.home_currency,
            pairs=self.pairs,
            equity=self.equity
        )
        self.toContinue = True
        initializeDecimalContext()

    def _setup_datafeed(self, datafeed: datafeed_params) -> DataFeeder:
        _module = import_module('savoia.datafeed.datafeed')
        
        _params = datafeed['params']
        _params['pairs'] = self.pairs
        _params['feed_q'] = self.feed_q

        df = getattr(_module, datafeed['module_name'])
        return df(**_params)

    def _setup_execution(self, execution: execution_params) \
            -> ExecutionHandler:
        _module = import_module('savoia.execution.execution')
        
        _params = execution['params']
        _params['event_q'] = self.event_q
        _params['exec_q'] = self.exec_q

        exe = getattr(_module, execution['module_name'])
        return exe(**_params)

    def _setup_strategy(self, strategy: strategy_params) \
            -> ExecutionHandler:
        _module = import_module('savoia.strategy.strategy')
        
        _params = strategy['params']
        _params['pairs'] = self.pairs
        _params['event_q'] = self.event_q

        exe = getattr(_module, strategy['module_name'])
        return exe(**_params)

    def _setup_result(self, result: result_params) -> ResultHandler:
        _module = import_module('savoia.result.result')
        
        _params = result['params']
        _params['pairs'] = self.pairs
        _params['result_q'] = self.result_q

        exe = getattr(_module, result['module_name'])
        return exe(**_params)

    def _run_engine(self) -> None:
        """
        Carries out an infinite while loop that polls the
        event_q queue and directs each event to either the
        strategy component of the execution handler. The
        loop will then pause for "heartbeat" seconds and
        continue until the maximum number of iterations is
        exceeded.
        """
        _wait: bool = False
        self.logger.info("Running engine...")
        while self.iters < self.max_iters and self.toContinue:
            try:
                event = self.event_q.get(_wait)
            except Empty:
                try:
                    tick_event = self.feed_q.get(False)
                except Empty:
                    pass
                else:
                    if tick_event is None:
                        self.logger.info('Acknowledged the end of datafeed.')
                        self.toContinue = False
                    elif tick_event.type != 'TICK':
                        raise Exception
                    else:
                        self.logger.debug('Process TICK -%s' % tick_event)
                        self.ticker.update_ticker(tick_event)
                        self.portfolio.update_portfolio(tick_event)
                        self.strategy.calculate_signals(tick_event)
            else:
                _wait = False
                if event is not None:
                    if event.type == 'SIGNAL':
                        self.logger.info("Process SIGNAL -%s" % event)
                        self.portfolio.execute_signal(event)
                    elif event.type == 'ORDER':
                        self.logger.info("Process ORDER -%s" % event)
                        self.exec_q.put(event)
                        _wait = self.isBacktest
                    elif event.type == 'FILL':
                        self.logger.info("Process FILL -%s" % event)
                        self.portfolio.execute_fill(event)
                    else:
                        raise Exception
            time.sleep(self.heartbeat)
            self.iters += 1
        self.exec_q.put(None)
        return

    def _output_performance(self) -> None:
        """
        Outputs the strategy performance from the backtest.
        """
        self.logger.info("Calculating Performance Metrics...")
        self.portfolio.output_results()

    def _run(self) -> None:
        _result = threading.Thread(target=self.result.run)
        _datafeed = threading.Thread(target=self.datafeed.run)
        _execution = threading.Thread(target=self.execution.run)
        _engine = threading.Thread(target=self._run_engine)

        _result.start()
        _execution.start()
        _engine.start()
        _datafeed.start()

        _datafeed.join()
        _engine.join()
        _execution.join()
        self.result_q.put(None)
        _result.join()

    def run(self) -> None:
        """
        Runs the engine.
        """
        if self.isBacktest:
            _start = time.time()
            self.logger.info('Start Backtesting.')
            self._run()
            # self._output_performance()
            self.logger.info("Backtest complete. Elapsed Time[Sec]: " +
                f'{time.time() - _start}')
        else:
            self.logger.info('Start Live trading.')
            self._run()
            self.logger.info("Trading complete.")
