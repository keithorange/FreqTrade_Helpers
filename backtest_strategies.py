import argparse
import sys
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


def backtest_strategies(strategies, batch_size):
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
        success_tracker[strategy] = "error"  # f"Error(1000 ch): {error_message[-1000:]} "
    save_success_tracker(success_tracker)


def find_pending_strategies(tracker, retry_errors=False):
    """Lists strategies that haven't been successfully processed or have errors, based on the retry_errors flag."""
    pending_strategies = [name for name, status in tracker.items() if status == 0]
    if retry_errors:
        error_strategies = [name for name, status in tracker.items() if status == "error"]
        for strategy in error_strategies:
            tracker[strategy] = 0  # Reset the status to 0 for retrying
        pending_strategies.extend(error_strategies)
    return pending_strategies


# Set up argparse to handle command line arguments
parser = argparse.ArgumentParser(description="Backtest strategies.")
parser.add_argument('--retry_errors', action='store_true',
                    help="Retry strategies that previously encountered errors.")
parser.add_argument('--batch_size', type=int, default=20,
                    help="Number of strategies to process in each batch. Default is 20.")

args = parser.parse_args()

# Modify the main block to use the parsed arguments
if __name__ == "__main__":
    initialize_directories()
    success_tracker = initialize_success_tracker()

    # Use args.retry_errors to check if retry_errors was specified
    retry_errors = args.retry_errors

    # Use args.batch_size for the batch size, defaulting to 20 if not provided
    batch_size = args.batch_size

    pending_strategies = find_pending_strategies(success_tracker, retry_errors=retry_errors)
    print(f"Pending strategies: {pending_strategies}")

    backtest_strategies(pending_strategies, batch_size=batch_size)

    # Save any updates made to the success tracker
    save_success_tracker(success_tracker)

    print(f"Backtesting completed. Results stored in {RESULTS_DIR}")
