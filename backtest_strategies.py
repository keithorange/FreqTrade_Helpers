import os
import subprocess
from pathlib import Path
import json
from tqdm import tqdm  # Import tqdm for progress tracking

# Constants
STRATEGY_DIR = "user_data/strategies"
RESULTS_DIR = "MY_HELPER_SCRIPTS/MY_BACKTESTING_RESULTS"
SUCCESS_TRACKER_FILE = Path(RESULTS_DIR) / "success_tracker.json"


def initialize_directories():
    """Ensures that the results directory exists."""
    Path(RESULTS_DIR).mkdir(parents=True, exist_ok=True)


def initialize_success_tracker():
    """Initializes or loads the success tracker."""
    if SUCCESS_TRACKER_FILE.exists():
        with open(SUCCESS_TRACKER_FILE, 'r') as file:
            return json.load(file)
    else:
        return {file[:-3]: 0 for file in os.listdir(STRATEGY_DIR) if file.endswith(".py")}


def save_success_tracker(tracker):
    """Saves the success tracker to file."""
    with open(SUCCESS_TRACKER_FILE, 'w') as file:
        json.dump(tracker, file, indent=4)


def find_pending_strategies(tracker):
    """Lists strategies that haven't been successfully processed."""
    return [name for name, status in tracker.items() if status == 0]


def backtest_strategies(strategies, batch_size=10):
    """Backtests strategies in batches."""
    for batch in tqdm([strategies[i:i + batch_size] for i in range(0, len(strategies), batch_size)], desc="Backtesting"):
        execute_backtest_batch(batch)


def execute_backtest_batch(strategy_batch):
    """Executes backtesting for a batch of strategies and logs results."""
    command = ['./run_backtest.sh', " ".join(strategy_batch)]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            extract_and_save_results(strategy_batch)
        else:
            log_error(strategy_batch, result.stderr)
    except Exception as e:
        log_error(strategy_batch, str(e))


def extract_and_save_results(strategy_batch):
    """Extracts backtesting results for each strategy and saves them."""
    # Read in all files starting with 'BACKTESTING_RESULT'
    backtest_files = [f for f in os.listdir(os.getcwd()) if f.startswith('BACKTESTING_RESULT')]

    # Filter out and delete .meta.json files
    meta_files = [f for f in backtest_files if f.endswith('.meta.json')]
    for meta_file in meta_files:
        os.remove(os.path.join(os.getcwd(), meta_file))
        print(f"Deleted {meta_file}.")

    # Remaining files should only be .json files (excluding .meta.json files)
    backtest_json_files = [f for f in backtest_files if not f.endswith('.meta.json')]

    if not backtest_json_files:
        print("No BACKTESTING_RESULT.json files found.")
        return

    # Sort JSON files to find the latest
    backtest_json_files.sort(reverse=True)
    latest_result_file = backtest_json_files[0]

    with open(os.path.join(os.getcwd(), latest_result_file), 'r') as file:
        results = json.load(file).get("strategy_comparison", [])

    for strategy in strategy_batch:
        result = next((item for item in results if item.get("key") == strategy), None)
        if result:
            with open(Path(RESULTS_DIR) / f"{strategy}_result.json", 'w') as result_file:
                json.dump(result, result_file, indent=4)
            success_tracker[strategy] = 1
            print(f"Results saved for strategy: {strategy}")
        else:
            success_tracker[strategy] = "No results found"
            print(f"No results found for strategy: {strategy}")

    # Update and save the success tracker
    save_success_tracker(success_tracker)

    # Delete the .json file used for extracting results
    os.remove(os.path.join(os.getcwd(), latest_result_file))
    print(f"Deleted {latest_result_file} after processing.")


def log_error(strategy_batch, error_message):
    """Logs errors for strategies in the batch."""
    for strategy in strategy_batch:
        print(f"Error for {strategy}: {error_message}")
        success_tracker[strategy] = error_message
    save_success_tracker(success_tracker)


if __name__ == "__main__":
    initialize_directories()
    success_tracker = initialize_success_tracker()
    pending_strategies = find_pending_strategies(success_tracker)
    print(f"Pending strategies: {pending_strategies}")
    backtest_strategies(pending_strategies)
    print(f"Backtesting completed. Results stored in {RESULTS_DIR}")


# import os
# import subprocess
# from pathlib import Path
# import json
# from tqdm import tqdm  # Import tqdm for progress tracking

# # Directory where the strategy files are stored
# strategy_dir = "user_data/strategies"
# # Temporary directory to store the test results
# test_results_dir = "MY_HELPER_SCRIPTS/MY_BACKTESTING_RESULTS"
# # File to track global success
# success_tracker_file = Path(test_results_dir) / "success_tracker.json"

# # Ensure the test results directory exists
# Path(test_results_dir).mkdir(parents=True, exist_ok=True)

# # Initialize or load the success tracker
# if success_tracker_file.exists():
#     with open(success_tracker_file, 'r') as file:
#         success_tracker = json.load(file)
# else:
#     success_tracker = {}
#     # Pre-populate the success tracker with strategies set to 0
#     for file in os.listdir(strategy_dir):
#         if file.endswith(".py"):
#             strategy_name = file[:-3]  # Exclude the '.py' extension
#             success_tracker[strategy_name] = 0
#     # Save the initialized success tracker
#     with open(success_tracker_file, 'w') as file:
#         json.dump(success_tracker, file, indent=4)


# def list_strategies(directory):
#     """List all .py files in the given directory and extract strategy names."""
#     strategies = []
#     for strategy_name, status in success_tracker.items():
#         if status == 0:  # Only include strategies that haven't been successfully processed
#             strategies.append(strategy_name)
#     return strategies


# def batch_backtest(strategies, batch_size):
#     """Process strategies in batches and execute backtesting."""
#     for i in tqdm(range(0, len(strategies), batch_size), desc="Processing batches"):
#         batch = strategies[i:i + batch_size]
#         execute_backtest(batch)


# def log_results(strategy_batch):
#     """
#     Reads the BACKTESTING_RESULT.json and extracts results for each strategy,
#     then saves the result for each strategy in a separate JSON file.
#     """
#     results_file_path = os.path.join(os.getcwd(), 'BACKTESTING_RESULT.json')
#     with open(results_file_path, 'r') as file:
#         backtesting_results = json.load(file)

#     strategy_comparisons = backtesting_results.get("strategy_comparison", [])

#     for strategy in strategy_batch:
#         # Find the result object for the current strategy
#         strategy_result = next(
#             (item for item in strategy_comparisons if item.get("key") == strategy), None)

#         if strategy_result:
#             # Path for the strategy-specific result file
#             result_file_path = Path(test_results_dir) / f"{strategy}_result.json"
#             with open(result_file_path, 'w') as result_file:
#                 json.dump(strategy_result, result_file, indent=4)
#                 print(f"Results saved for strategy: {strategy}")
#                 success_tracker[strategy] = 1  # Mark strategy as successfully backtested
#         else:
#             print(f"No results found for strategy: {strategy}")
#             success_tracker[strategy] = "No results found"

#     # Update the global success tracker file after processing the batch
#     with open(success_tracker_file, 'w') as file:
#         json.dump(success_tracker, file, indent=4)


# def execute_backtest(strategy_batch):
#     strategies_str = " ".join(strategy_batch)
#     command = ['./run_backtest.sh', strategies_str]
#     try:
#         result = subprocess.run(command, capture_output=True, text=True)
#         if result.returncode == 0:
#             # Call log_results function after successful execution
#             log_results(strategy_batch)
#         else:
#             error = result.stderr
#             print(f"Error executing backtest for batch {strategy_batch}: {error}")
#             for strategy in strategy_batch:
#                 success_tracker[strategy] = error  # Log the error for the strategy
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#         for strategy in strategy_batch:
#             success_tracker[strategy] = str(e)  # Log the exception as the error for the strategy

#     # Update the global success tracker file after each batch
#     with open(success_tracker_file, 'w') as file:
#         json.dump(success_tracker, file, indent=4)


# # Adjust the main section to call batch_backtest with all strategies
# if __name__ == "__main__":
#     strategies = list_strategies(strategy_dir)  # Load strategies from the directory
#     print(f"Found strategies: {strategies}")
#     batch_backtest(strategies, batch_size=10)  # Process all strategies in batches
#     print(f"Backtesting completed. Results stored in {test_results_dir}")
