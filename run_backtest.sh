#!/bin/bash
source .venv/bin/activate
freqtrade backtesting \
    --strategy-list $1 \
    --fee 0.001 \
    --timerange 20230101-20230201 \
    --config user_data/configs/config_binance_backtest.json \
    --config user_data/configs/config_static_pairlist.json \
    --timeframe 5m \
    --export trades \
    --export-filename BACKTESTING_RESULT.json \
    --pairs BTC/USDT SOL/USDT ETH/USDT
