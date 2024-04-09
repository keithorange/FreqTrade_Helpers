from tqdm import tqdm
import webbrowser
from multiprocessing import Pool, Manager
import time
import sys
import random
import subprocess
import os
import json


def kill_freqtrade_sessions(strategy_objects):
    for strategy_object in strategy_objects:
        strategy_name = strategy_object['name']
        print(f"Killing Freqtrade sessions for {strategy_name}...")
        subprocess.run(["pkill", "-f", f"freqtrade trade.*-s {strategy_name}"])
    print("All specified Freqtrade sessions terminated.")


def run_strategy(strategy_object, base_config, configs_dir, database_dir, port):
    strategy_name = strategy_object['name']
    total_profit_percent = strategy_object['total_profit_percent']
    timeframe = strategy_object['timeframe']

    random_port = int(port)
    print(
        f"Launching {strategy_name} strategy on port {random_port} with total profit% {total_profit_percent}...")

    strategy_config = dict(base_config)
    strategy_config['timeframe'] = timeframe
    strategy_config['api_server']['listen_port'] = random_port

    """
    "internals": {
        "process_throttle_secs": 10
    }
    """
    # TO AVOID _async_get_candle_history() returned exception: "kraken {"error":["EGeneral:Too many requests"]}" WAIT LONGER BETWEEN REQUESTS
    # Unnnecessary
    # # TODO: make faster for less pairs, slower for more pairs
    # if timeframe == '1m':
    #     strategy_config['internals']['process_throttle_secs'] = 5

    # elif timeframe == '5m':
    #     strategy_config['internals']['process_throttle_secs'] = 7

    strategy_config_path = os.path.join(configs_dir, f'config_{strategy_name}.json')
    with open(strategy_config_path, 'w') as file:
        json.dump(strategy_config, file, indent=4)

    cmd = [
        'freqtrade', 'trade', '-c', strategy_config_path,
        '-s', strategy_name,
        '--db-url', f'sqlite:///{database_dir}{strategy_name}.live.sqlite'
    ]
    subprocess.run(cmd)


def select_top_strategies(strategy_objects, max_processes):
    # Sort the strategy objects by total profit percentage in descending order
    sorted_strategies = sorted(
        strategy_objects, key=lambda x: x['total_profit_percent'], reverse=True)
    # Select the top strategies up to the max number of parallel processes
    return sorted_strategies[:max_processes]


if __name__ == '__main__':
    # strategy_objects_updated = [
    #     {"name": "BinHV45_755", "timeframe": "1m", "total_profit_percent": 4.25},  # Updated name
    #     {"name": "ClucHAnix_0", "timeframe": "1m", "total_profit_percent": 7.11},
    #     {"name": "ClucHAnix_6", "timeframe": "1m", "total_profit_percent": 6.92},
    #     {"name": "ClucHAnix_748", "timeframe": "1m", "total_profit_percent": 4.82},
    #     {"name": "ClucHAnix_BB_RPB_MOD2", "timeframe": "1m", "total_profit_percent": 14.61},
    #     {"name": "ClucHAnix_BB_RPB_MOD_CTT", "timeframe": "1m", "total_profit_percent": 12.92},
    #     {"name": "CombinedBinHAndClucHyperV0", "timeframe": "1m",
    #         "total_profit_percent": 4.04},  # Updated name
    #     {"name": "Discord_1_ClucHAnix", "timeframe": "1m", "total_profit_percent": 8.60},
    #     {"name": "Discord_BinHV45HyperOpted", "timeframe": "1m",
    #         "total_profit_percent": 4.97},  # Updated name
    #     {"name": "MiniLambo", "timeframe": "1m", "total_profit_percent": 5.57},
    #     {"name": "BBMod1", "timeframe": "5m", "total_profit_percent": 4.04},  # Updated name
    #     {"name": "BB_RPB_TSL_RNG", "timeframe": "5m", "total_profit_percent": 4.06},
    #     {"name": "ClucHAnix_5M_E0V1E_DYNAMIC_TB", "timeframe": "5m",
    #         "total_profit_percent": 6.18},  # Updated name
    #     {"name": "ClucHAnix_5mTB1", "timeframe": "5m", "total_profit_percent": 7.28},  # Updated name
    #     {"name": "ClucHAnix_5m_4", "timeframe": "5m", "total_profit_percent": 9.04},
    #     {"name": "ClucHAnix_BB_RPB_MOD2_ROI", "timeframe": "5m",
    #         "total_profit_percent": 6.67},  # Updated name and profit% assumed
    #     {"name": "ClucHAnix_hhll_66", "timeframe": "5m", "total_profit_percent": 5.05},
    #     {"name": "Combined_NFIv6_SMA", "timeframe": "5m", "total_profit_percent": 4.40},
    #     {"name": "Combined_NFIv7_SMA_bAdBoY_20211030", "timeframe": "5m",
    #         "total_profit_percent": 5.40},  # Updated name
    #     {"name": "Discord_1_ClucHAnix5m", "timeframe": "5m", "total_profit_percent": 7.69},
    #     {"name": "ElliotV4Changed", "timeframe": "5m", "total_profit_percent": 4.05},
    #     {"name": "ElliotV5HO", "timeframe": "5m", "total_profit_percent": 6.14},
    #     {"name": "NFI5MOHO_WIP", "timeframe": "5m", "total_profit_percent": 4.60},
    #     {"name": "NFIV7_SMA", "timeframe": "5m", "total_profit_percent": 4.71},
    #     {"name": "NostalgiaForInfinityV7_SMA", "timeframe": "5m",
    #         "total_profit_percent": 4.76},  # Updated name
    #     {"name": "NotAnotherSMAOffsetStrategyHO_113", "timeframe": "5m",
    #         "total_profit_percent": 6.03},  # Updated name and profit% assumed
    #     {"name": "NotAnotherSMAOffsetStrategyHOv3", "timeframe": "5m",
    #         "total_profit_percent": 5.72},  # Updated name and profit% assumed
    #     {"name": "NotAnotherSMAOffsetStrategyHOv3_b", "timeframe": "5m",
    #         "total_profit_percent": 4.75},  # Updated name and profit% assumed
    #     {"name": "NotAnotherSMAOffsetStrategy_199", "timeframe": "5m",
    #         "total_profit_percent": 6.10},  # Updated name and profit% assumed
    #     {"name": "NotAnotherSMAOffsetStrategy_uzi3", "timeframe": "5m",
    #         "total_profit_percent": 4.74},  # Updated name and profit% assumed
    #     {"name": "SMAOG", "timeframe": "5m", "total_profit_percent": 4.40},
    #     {"name": "SMAOffset", "timeframe": "5m", "total_profit_percent": 4.56},
    #     {"name": "newstrategy4", "timeframe": "5m", "total_profit_percent": 4.17},
    #     {"name": "tesla", "timeframe": "5m", "total_profit_percent": 4.22},
    #     {"name": "true_lambo_2", "timeframe": "5m", "total_profit_percent": 4.83},
    #     ]

    strategy_objects_updated = [
                    {"name": "BinHV45_755", "timeframe": "1m",
                        "total_profit_percent": 4.25},  # Updated name
                    {"name": "ClucHAnix_0", "timeframe": "1m", "total_profit_percent": 7.11},
                    {"name": "ClucHAnix_6", "timeframe": "1m", "total_profit_percent": 6.92},
                    {"name": "ClucHAnix_748", "timeframe": "1m", "total_profit_percent": 4.82},
                    {"name": "ClucHAnix_BB_RPB_MOD2", "timeframe": "1m", "total_profit_percent": 14.61},
                    {"name": "ClucHAnix_BB_RPB_MOD2", "timeframe": "1m", "total_profit_percent": 12.92},
                    {"name": "CombinedBinHAndClucHyperV0", "timeframe": "1m",
                     "total_profit_percent": 4.04},  # Updated name
                    {"name": "Discord_1_ClucHAnix", "timeframe": "1m", "total_profit_percent": 8.60},
                    {"name": "Discord_BinHV45HyperOpted", "timeframe": "1m",
                     "total_profit_percent": 4.97},  # Updated name
                    {"name": "MiniLambo", "timeframe": "1m", "total_profit_percent": 5.57},
                    {"name": "BBMod1", "timeframe": "5m", "total_profit_percent": 4.04},  # Updated name
        {"name": "BB_RPB_TSL_RNG", "timeframe": "5m", "total_profit_percent": 4.06},

        {"name": "ClucHAnix_5m_4", "timeframe": "5m", "total_profit_percent": 9.04},
        {"name": "ClucHAnix_BB_RPB_MOD2_ROI", "timeframe": "5m",
                        "total_profit_percent": 6.67},  # Updated name and profit% assumed
        {"name": "ClucHAnix_hhll_66", "timeframe": "5m", "total_profit_percent": 5.05},
        {"name": "Combined_NFIv6_SMA", "timeframe": "5m", "total_profit_percent": 4.40},
        {"name": "Combined_NFIv7_SMA_bAdBoY_20211204", "timeframe": "5m",
                        "total_profit_percent": 5.40},  # Updated name
        {"name": "ElliotV4Changed", "timeframe": "5m", "total_profit_percent": 4.05},
        {"name": "ElliotV5HO", "timeframe": "5m", "total_profit_percent": 6.14},
        {"name": "NFI5MOHO_WIP", "timeframe": "5m", "total_profit_percent": 4.60},
        {"name": "NostalgiaForInfinityV7_SMAv2_1", "timeframe": "5m", "total_profit_percent": 4.71},
        {"name": "NostalgiaForInfinityV7_SMA", "timeframe": "5m",
                        "total_profit_percent": 4.76},  # Updated name
        {"name": "NotAnotherSMAOffsetStrategyHO_113", "timeframe": "5m",
                        "total_profit_percent": 6.03},  # Updated name and profit% assumed
        {"name": "NotAnotherSMAOffsetStrategyHOv3", "timeframe": "5m",
                        "total_profit_percent": 5.72},  # Updated name and profit% assumed
        {"name": "NotAnotherSMAOffsetStrategyHOv3_b", "timeframe": "5m",
                        "total_profit_percent": 4.75},  # Updated name and profit% assumed
        {"name": "NotAnotherSMAOffsetStrategy_199", "timeframe": "5m",
                        "total_profit_percent": 6.10},  # Updated name and profit% assumed
        {"name": "NotAnotherSMAOffsetStrategy_uzi3", "timeframe": "5m",
                        "total_profit_percent": 4.74},  # Updated name and profit% assumed
        {"name": "SMAOG", "timeframe": "5m", "total_profit_percent": 4.40},
        {"name": "SMAOffset", "timeframe": "5m", "total_profit_percent": 4.56},
        {"name": "newstrategy4", "timeframe": "5m", "total_profit_percent": 4.17},
        {"name": "tesla", "timeframe": "5m", "total_profit_percent": 4.22},
        {"name": "true_lambo", "timeframe": "5m", "total_profit_percent": 4.83},
        ]

    """

    Based on the sorted list of strategies by their total profit percentages, if you were to run the script right now, the top 12 strategies selected for launch would be:

    ClucHAnix_BB_RPB_MOD2 (1m) - 14.61%
    ClucHAnix_BB_RPB_MOD_CTT (1m) - 12.92%
    ClucHAnix_5m_4 (5m) - 9.04%
    Discord_1_ClucHAnix (1m) - 8.60%
    Discord_1_ClucHAnix5m (5m) - 7.69%
    ClucHAnix_5mTB1 (5m) - 7.28%
    ClucHAnix_0 (1m) - 7.11%
    ClucHAnix_6 (1m) - 6.92%
    ClucHAnix_BB_RPB_MOD2_ROI (5m) - 6.67%
    ClucHAnix_5M_E0V1E_DYNAMIC_TB (5m) - 6.18%
    ElliotV5HO (5m) - 6.14%
    NotAnotherSMAOffsetStrategy_199 (5m) - 6.10%

    """
    config_base_path = 'user_data/configs/config_kraken_backtest.json'
    new_configs_dir = 'user_data/configs/generated/'
    db_dir = 'user_data/db/'
    os.makedirs(new_configs_dir, exist_ok=True)
    os.makedirs(db_dir, exist_ok=True)

    with open(config_base_path, 'r') as file:
        base_config = json.load(file)

    # TODO: shrink: 12 good mid range no ddoss hits! 35 works but may fail to hit every candle
    max_parallel_processes = 12

    if '--kill' in sys.argv:
        kill_freqtrade_sessions(strategy_objects_updated)
    else:
        selected_strategies = select_top_strategies(
            strategy_objects_updated, max_parallel_processes)

        print("\nLaunching Strategies. API URLs:")

        initial_port = 6900  # Start from this port

        strategy_url_mappings = {}
        for i, strategy_object in enumerate(selected_strategies):
            port = initial_port + i
            print(f"Launching {strategy_object['name']} strategy on port {port}...")

            url = f"http://localhost:{port}"
            strategy_url_mappings[strategy_object['name']] = url
            print(f"Strategy: {strategy_object['name']} URL: {url}")

        with open('strategy_url_mappings.json', 'w') as file:
            json.dump(strategy_url_mappings, file, indent=4)

        args_list = [(strategy_object, base_config, new_configs_dir, db_dir, port)
                     for strategy_object, port in zip(selected_strategies, range(initial_port, initial_port + len(selected_strategies)))]

        with Manager():
            with Pool(processes=min(len(selected_strategies), max_parallel_processes)) as pool:
                launched_strategies_count = 0  # Counter for the number of launched strategies

                for args in args_list:
                    # Clear screen
                    os.system('cls' if os.name == 'nt' else 'clear')

                    launched_strategies_count += 1  # Increment the counter for each launched strategy
                    print(f"Launching {args[0]['name']} strategy on port {args[4]}...")
                    # Print the progress bar based on the number of launched strategies
                    print(
                        f"PROGRESS | {'=' * launched_strategies_count}{' ' * (len(selected_strategies) - launched_strategies_count)} | {launched_strategies_count}/{len(selected_strategies)}")

                    pool.apply_async(run_strategy, args=args)
                    # Introduce a random delay before launching the next task
                    time.sleep(random.random() * 5 + 1)

                pool.close()
                pool.join()  # Wait for all the processes to finish

        print(f"DONE: Launched {len(selected_strategies)} strategies.")
