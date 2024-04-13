import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Load the data
file_path = 'MY_HELPER_SCRIPTS/MY_BACKTESTING_RESULTS/TOP_STRATEGIES/results.csv'
data = pd.read_csv(file_path)

# Convert 'duration_avg' to Timedelta for comparison and apply filters
data['duration_avg'] = pd.to_timedelta(data['duration_avg'])
data = data[(data['duration_avg'] <= pd.Timedelta(days=7)) &
            (data['trades'] >= 30) & (data['positive_ev'] > 2)]

# Select columns relevant for clustering
features = data[['profit_mean', 'profit_mean_pct', 'profit_sum', 'profit_sum_pct',
                 'profit_total_abs', 'profit_total', 'profit_total_pct',
                 'max_drawdown_account', 'winrate']]

# Standardize the data
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features)

# Apply K-means clustering
kmeans = KMeans(n_clusters=20, random_state=0)
clusters = kmeans.fit_predict(features_scaled)

# Add cluster information to the original dataframe
data['cluster'] = clusters

# Function to select the most profitable strategy from each cluster


def select_top_strategies(df, n_strategies=1):
    selected_strategies = pd.DataFrame()
    for cluster in df['cluster'].unique():
        cluster_data = df[df['cluster'] == cluster]
        top_strategies = cluster_data.nlargest(n_strategies, 'profit_total_pct')
        selected_strategies = pd.concat([selected_strategies, top_strategies], axis=0)
    return selected_strategies


# Select the most profitable strategy from each cluster
top_strategies = select_top_strategies(data)
top_strategies['timeframe'] = '5m'  # Add hardcoded 'timeframe'
print(top_strategies)

# Save to CSV
csv_output_path = 'selected_top_strategies.csv'
top_strategies.to_csv(csv_output_path, index=False)
