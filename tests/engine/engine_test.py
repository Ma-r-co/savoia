from savoia.engine.engine import Engine, datafeed_params, \
    execution_params, strategy_params, engine_params
from savoia.config.dir_config import CSV_DATA_DIR

from decimal import Decimal
import logging.config
import os
import json

import pytest


@pytest.mark.skip()
def test_engine_run() -> None:
    def setup_logging() -> None:
        """Setup logging configuration"""
        path = os.path.join('/Users/makoto/Pywork/savoia/src/savoia/config',
            'logging.json')
        if os.path.exists(path):
            with open(path, 'rt') as f:
                config = json.load(f)
                logging.config.dictConfig(config)
        else:
            raise FileNotFoundError('Not exist : %s' % path)

    datafeed: datafeed_params = {
        'module_name': 'HistoricCSVDataFeeder',
        'params': {
            'csv_dir': CSV_DATA_DIR,
        }
    }

    execution: execution_params = {
        'module_name': 'SimulatedExecution',
        'params': {
            'heartbeat': 0
        }
    }

    strategy: strategy_params = {
        'module_name': 'DummyStrategy',
        'params': {}
    }

    engine: engine_params = {
        'pairs': ['GBPUSD', 'USDJPY'],
        'home_currency': 'JPY',
        'equity': Decimal(10 ** 6),
        'isBacktest': True,
        'max_iters': 10 ** 7,
        'heart_beat': 0
    }

    eg = Engine(
        engine=engine,
        datafeed=datafeed,
        execution=execution,
        strategy=strategy
    )

    setup_logging()
    eg.run()


if __name__ == '__main__':
    test_engine_run()
