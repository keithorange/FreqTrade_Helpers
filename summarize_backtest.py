import os
import json
from pathlib import Path
from tabulate import tabulate
import sys  # Import sys for exiting the script


def generate_summary(directory='MY_HELPER_SCRIPTS/MY_BACKTESTING_RESULTS'):
    results = []
    for filename in os.listdir(directory):
        if filename.endswith('_result.json'):
            filepath = Path(directory) / filename
            with open(filepath, 'r') as file:
                data = json.load(file)
                results.append(data)

    def sort_by(x):
        return x['profit_total_pct']

    # Attempt to sort the results, catching any KeyError
    try:
        sorted_results = sorted(results, key=sort_by, reverse=True)
    except KeyError as e:
        # Print the error message and exit
        print(f"Error while processing files: {e}")
        print("One or more files may be missing the 'profit_total_pct' key.")
        sys.exit(1)  # Exit the script with an error code

    # Assuming all results have the same structure, use the keys from the first result as headers
    headers = sorted_results[0].keys()

    table_data = [list(result.values()) for result in sorted_results]
    summary_table = tabulate(table_data, headers=headers, tablefmt="grid")

    # Print and save the summary table
    print(summary_table)
    summary_filepath = Path(directory) / 'summary_results.txt'
    with open(summary_filepath, 'w') as file:
        file.write(summary_table)
    print(f"Summary saved to {summary_filepath}")


# Call the function to generate the summary
generate_summary()
