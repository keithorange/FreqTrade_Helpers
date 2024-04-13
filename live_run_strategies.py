import pandas as pd
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
        strategy_name = strategy_object['strategy_name']
        print(f"Killing Freqtrade sessions for {strategy_name}...")
        subprocess.run(["pkill", "-f", f"freqtrade trade.*-s {strategy_name}"])
    print("All specified Freqtrade sessions terminated.")


def run_strategy(strategy_object, base_config, configs_dir, database_dir, port):
    strategy_name = strategy_object['strategy_name']
    positive_ev = strategy_object['positive_ev']
    timeframe = strategy_object['timeframe']

    random_port = int(port)
    print(
        f"Launching {strategy_name} strategy on port {random_port} with total profit% {positive_ev}...")

    strategy_config = dict(base_config)
    strategy_config['timeframe'] = timeframe
    strategy_config['api_server']['listen_port'] = random_port


    if timeframe == '1m':
        strategy_config['internals']['process_throttle_secs'] = 5

    elif timeframe == '5m':
        strategy_config['internals']['process_throttle_secs'] = 45

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
        strategy_objects, key=lambda x: x['positive_ev'], reverse=True)
    # Select the top strategies up to the max number of parallel processes
    return sorted_strategies[:max_processes]

    import subprocess

import requests
def make_ping_request(url, retry=3):
    for attempt in range(retry):
        try:
            response = requests.get(url)
            print(f"Response: {response}")
            print(f"status code: {response.status_code} raw: {response.raw}")
            if response.status_code == 200:
                print(f"Successful ping to {url}. Response: {response.text}")
                return True
            else:
                print(f"Server responded with status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"Attempt {attempt + 1}: Failed to ping {url}. Error: {e}")
        time.sleep(5)  # Wait before retrying
    return False

if __name__ == '__main__':
    # Load the CSV file
    top_strategies_loaded = pd.read_csv('selected_top_strategies.csv')

    # Convert DataFrame to a list of dictionaries
    strategies_list = top_strategies_loaded.to_dict(orient='records')

    # # Display each dictionary
    # for strategy in strategies_list:
    #     print(strategy)

    strategy_objects_updated = strategies_list

    print(f"ensure you activate venv!")
    # maybe not
    # subprocess.call(["source", ".venv/bin/activate"], shell=True)

    config_base_path = 'user_data/configs/config_kraken_backtest.json'
    new_configs_dir = 'user_data/configs/generated/'
    db_dir = 'user_data/db/'
    os.makedirs(new_configs_dir, exist_ok=True)
    os.makedirs(db_dir, exist_ok=True)

    with open(config_base_path, 'r') as file:
        base_config = json.load(file)

    # TODO: shrink: 12 good mid range no ddoss hits! 35 works but may fail to hit every candle
    max_parallel_processes = 3

    if '--kill' in sys.argv:
        kill_freqtrade_sessions(strategy_objects_updated)
    else:
        # selected_strategies = select_top_strategies(
        #     strategy_objects_updated, max_parallel_processes)

        # print("\nLaunching Strategies. API URLs:")

        # initial_port = 6900  # Start from this port

        # strategy_url_mappings = {}
        
        # for i, strategy_object in enumerate(selected_strategies):
        #     port = initial_port + i
        #     #print(f"Launching {strategy_object['strategy_name']} strategy on port {port}...")

        #     url = f"http://localhost:{port}"
        #     strategy_url_mappings[strategy_object['strategy_name']] = url
        #     #print(f"Strategy: {strategy_object['strategy_name']} URL: {url}")

        # with open('strategy_url_mappings.json', 'w') as file:
        #     json.dump(strategy_url_mappings, file, indent=4)

        # args_list = [(strategy_object, base_config, new_configs_dir, db_dir, port)
        #              for strategy_object, port in zip(selected_strategies, range(initial_port, initial_port + len(selected_strategies)))]

        # with Manager():
        #     with Pool(processes=min(len(selected_strategies), max_parallel_processes)) as pool:
        #         launched_strategies_count = 0  # Counter for the number of launched strategies

        #         for args in args_list:
        #             # # Clear screen
        #             # os.system('cls' if os.name == 'nt' else 'clear')

        #             launched_strategies_count += 1  # Increment the counter for each launched strategy
        #             print(f"Launching {args[0]['strategy_name']} strategy on port {args[4]}...")
        #             # Print the progress bar based on the number of launched strategies
        #             print(
        #                 f"PROGRESS | {'=' * launched_strategies_count}{' ' * (len(selected_strategies) - launched_strategies_count)} | {launched_strategies_count}/{len(selected_strategies)}")

                    
                    
        #             pool.apply_async(run_strategy, args=args)
                    
        #             # Introduce a random delay before launching the next task
        #             time.sleep(10)


        #         pool.close()
        #         pool.join()  # Wait for all the processes to finish
        
        def launch_strategies(strategy_objects_updated, max_parallel_processes, base_config, new_configs_dir, db_dir):
            selected_strategies = select_top_strategies(strategy_objects_updated, max_parallel_processes)

            print("\nLaunching Strategies. API URLs:")

            initial_port = 6900  # Start from this port
            strategy_url_mappings = create_strategy_url_mappings(selected_strategies, initial_port)

            with open('strategy_url_mappings.json', 'w') as file:
                json.dump(strategy_url_mappings, file, indent=4)

            args_list = create_args_list(selected_strategies, base_config, new_configs_dir, db_dir, initial_port)

            with Manager():
                with Pool(processes=min(len(selected_strategies), max_parallel_processes)) as pool:
                    launch_strategies_in_pool(pool, args_list, selected_strategies)

            return selected_strategies, strategy_url_mappings

        def create_strategy_url_mappings(selected_strategies, initial_port):
            strategy_url_mappings = {}
            for i, strategy_object in enumerate(selected_strategies):
                port = initial_port + i
                url = f"http://localhost:{port}"
                strategy_url_mappings[strategy_object['strategy_name']] = url
            return strategy_url_mappings


        def create_args_list(selected_strategies, base_config, new_configs_dir, db_dir, initial_port):
            return [(strategy_object, base_config, new_configs_dir, db_dir, port)
                    for strategy_object, port in zip(selected_strategies, range(initial_port, initial_port + len(selected_strategies)))]


        def launch_strategies_in_pool(pool, args_list, selected_strategies):
            launched_strategies_count = 0  # Counter for the number of launched strategies
            for args in args_list:
                launched_strategies_count += 1  # Increment the counter for each launched strategy
                print(f"Launching {args[0]['strategy_name']} strategy on port {args[4]}...")
                # Print the progress bar based on the number of launched strategies
                print_progress_bar(launched_strategies_count, selected_strategies)

                pool.apply_async(run_strategy, args=args)

                # Introduce a random delay before launching the next task
                time.sleep(10 + random.random()*10)

            pool.close()
            #pool.join()  # Wait for all the processes to finish


        def print_progress_bar(launched_strategies_count, selected_strategies):
            print(
                f"PROGRESS | {'=' * launched_strategies_count}{' ' * (len(selected_strategies) - launched_strategies_count)} | {launched_strategies_count}/{len(selected_strategies)}")


        # now going to ping so see which ones are up
            
        def make_ping_request(url):
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                return False
            return False

        def launch_and_ping_strategies(strategy_objects_updated, max_parallel_processes, base_config, new_configs_dir, db_dir):
            for attempt in range(3):
                print(f"Attempt {attempt + 1} to launch and ping strategies...")

                # Launch the strategies using the helper functions
                selected_strategies, strategy_url_mappings = launch_strategies(strategy_objects_updated, max_parallel_processes, base_config, new_configs_dir, db_dir)

                # Sleep a bit waiting for last stratagy to start
                time.sleep(10)
                # clear
                os.system('cls' if os.name == 'nt' else 'clear')
                not_up = []
                for strategy_name, url in strategy_url_mappings.items():
                    if not make_ping_request(url):
                        not_up.append(strategy_name)
                        print(f"Strategy {strategy_name} is not up at {url}")

                if not not_up:
                    print(f"DONE: Launched {len(selected_strategies)} strategies.")
                    return

                print(f"Failed to launch {len(not_up)} strategies. Retrying...")

            print(f"Failed to launch the following strategies after 3 attempts: {', '.join(not_up)}")
            
            
        launch_and_ping_strategies(strategy_objects_updated, max_parallel_processes, base_config, new_configs_dir, db_dir)