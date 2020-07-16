from abc import ABCMeta, abstractmethod
from logging import Logger, getLogger
import pandas as pd
import os
from queue import Queue, Empty
from decimal import Decimal

from typing import List, TextIO, Dict

from savoia.types.types import Pair


class Result(metaclass=ABCMeta):
    type: str
    time: pd.Timestamp


class EquityResult(Result):
    equity: Decimal
    balance: Decimal
    upl: Dict[str, Decimal]

    def __init__(self,
            time: pd.Timestamp,
            equity: Decimal,
            balance: Decimal,
            upl: Dict[str, Decimal]):
        self.type = 'EquityResult'
        self.time = time
        self.equity = equity
        self.balance = balance
        self.upl = upl


class ExecutionResult(Result):
    pair: Pair
    units: Decimal
    price: Decimal

    def __init__(self,
            time: pd.Timestamp,
            pair: Pair,
            units: Decimal,
            price: Decimal):
        self.type = 'ExecutionResult'
        self.time = time
        self.pair = pair
        self.units = units
        self.price = price


class ResultHandler(metaclass=ABCMeta):
    logger: Logger
    pairs: List[Pair]

    @abstractmethod
    def __init__(self, pairs: List[Pair], result_q: 'Queue[Result]'):
        self.logger = getLogger(__name__)
        self.pairs = pairs

    @abstractmethod
    def _write_EquityResult(self, result: EquityResult) -> None:
        pass

    @abstractmethod
    def _write_ExecutionResult(self, result: ExecutionResult) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass


class FileResultHandler(ResultHandler):
    '''
    FileResultHandler is to output results to files.
    '''
    pairs: List[Pair]
    output_dir: str
    equity_file: str
    equity_writer: TextIO
    execution_file: str
    execution_writer: TextIO

    def __init__(self, pairs: List[Pair], result_q: 'Queue[Result]',
            output_dir: str):
        self.logger = getLogger(__name__)
        self.pairs = pairs
        self.result_q = result_q
        self.output_dir = output_dir
        self.equity_file = 'Equity.csv'
        self.equity_writer = self._create_equity_writer(self.equity_file)
        self.execution_file = 'Execution.csv'
        self.execution_writer = self._create_execution_writer(
            self.execution_file
        )

    def _create_equity_writer(self, filename: str) -> TextIO:
        _out_file = open(os.path.join(self.output_dir, filename), 'w')
        _header: str = "Timestamp,Equity,Balance,UPL[Total]"
        for pair in self.pairs:
            _header += ",UPL[%s]" % pair
        _header += "\n"
        _out_file.write(_header)
        self.logger.info("Created equity file. Header as: %s", _header[:-1])
        return _out_file

    def _create_execution_writer(self, filename: str) -> TextIO:
        _out_file = open(os.path.join(self.output_dir, filename), "w")
        _header: str = "Timestamp,Pair,Units,Price\n"
        _out_file.write(_header)
        self.logger.info("Created execution file. Header as: %s", _header[:-1])
        return _out_file

    def _write_EquityResult(self, result: EquityResult) -> None:
        _line = f'{result.time},{result.equity},{result.balance}'
        _line += f',{result.upl["total"]}'
        for pair in self.pairs:
            _line += f',{result.upl[pair]}'
        _line += '\n'
        self.equity_writer.write(_line)
    
    def _write_ExecutionResult(self, result: ExecutionResult) -> None:
        _line = f'{result.time},{result.pair},{result.units},{result.price}\n'
        self.execution_writer.write(_line)
    
    def _close(self) -> None:
        self.execution_writer.close()
        self.equity_writer.close()

    def run(self) -> None:
        self.logger.info('FileResultHandler has started running...')
        while True:
            try:
                _result = self.result_q.get(block=True, timeout=5)
            except Empty:
                pass
            else:
                if _result is None:
                    # Close worker
                    break
                elif isinstance(_result, EquityResult):
                    try:
                        self._write_EquityResult(_result)
                    except Exception as e:
                        self.logger.error(
                            f'{e} - Unable to write EquityResult: {_result}'
                        )
                elif isinstance(_result, ExecutionResult):
                    try:
                        self._write_ExecutionResult(_result)
                    except Exception as e:
                        self.logger.error(
                            f'{e} - Unable to write ExecutionResult: {_result}'
                        )
                else:
                    self.logger.error(
                        f'Unexpected Result has been detected: {_result}'
                    )
        self._close()
        self.logger.info('FileResultHandler has completed...')
