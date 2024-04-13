import os
import json
import shutil
from pathlib import Path
from tabulate import tabulate
import sys


def generate_and_filter_summary(directory='MY_HELPER_SCRIPTS/MY_BACKTESTING_RESULTS', top_n=80):
    results = []
    for filename in os.listdir(directory):
        if filename.endswith('_result.json'):
            filepath = Path(directory) / filename
            with open(filepath, 'r') as file:
                data = json.load(file)

                profit_total_abs = float(data.get('profit_total_abs', 0))
                max_drawdown_abs = data.get('max_drawdown_abs')

                # Handle missing or zero max_drawdown_abs by setting positive_ev to profit_total_abs
                if max_drawdown_abs is None or float(max_drawdown_abs.replace('"', '')) == 0:
                    data['positive_ev'] = profit_total_abs
                else:
                    max_drawdown_abs = float(max_drawdown_abs.replace('"', ''))
                    data['positive_ev'] = profit_total_abs / max_drawdown_abs

                # rename "key" column to "strategy_name"
                data['strategy_name'] = data.pop('key')
                results.append(data)

    # Filter and sort results based on criteria, ignoring entries without positive_ev
    filtered_results = [res for res in results if 'positive_ev' in res and res['positive_ev']
                        > 0.5 and res['profit_total_abs'] > 100]

    sorted_filtered_results = sorted(
        filtered_results, key=lambda x: x['positive_ev'], reverse=True)[:top_n]

    # Print full data summary sorted by positive_ev
    sorted_results = sorted(results, key=lambda x: x.get('positive_ev', 0), reverse=True)
    print(tabulate([list(result.values()) for result in sorted_results],
          headers=sorted_results[0].keys(), tablefmt="grid"))

    # Print top 20 filtered results
    if sorted_filtered_results:
        print("\nTop 20 Results based on Positive EV and Profit Total Absolute:")
        print(tabulate([list(result.values()) for result in sorted_filtered_results],
              headers=sorted_filtered_results[0].keys(), tablefmt="grid"))
    else:
        print("\nNo results meet the filtering criteria.")

    import pandas as pd

    # ...

    if sorted_filtered_results:
        top_strategies_dir = Path(directory) / 'TOP_STRATEGIES/strategies'
        top_strategies_dir.mkdir(parents=True, exist_ok=True)

        for result in sorted_filtered_results:
            strategy_file = f"user_data/strategies/{result['strategy_name']}.py"

            #  copy strategy file to top_strategies_dir
            shutil.copy(strategy_file, top_strategies_dir / f"{result['strategy_name']}.py")

        summary_filepath = Path(directory) / 'TOP_STRATEGIES/results.txt'
        with open(summary_filepath, 'w') as file:
            file.write(tabulate([list(result.values()) for result in sorted_filtered_results],
                       headers=sorted_filtered_results[0].keys(), tablefmt="grid"))

        # Save the data to a CSV file
        df = pd.DataFrame(sorted_filtered_results)
        df.to_csv(Path(directory) / 'TOP_STRATEGIES/results.csv', index=False)
        # print
        print(
            f"Filtered summary and top strategy files have been saved to {top_strategies_dir} and {summary_filepath}, respectively.")


# Call the function to generate and filter the summary
generate_and_filter_summary()
