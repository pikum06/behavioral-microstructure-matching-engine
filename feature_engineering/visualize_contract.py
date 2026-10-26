# Generates graphs combining behvaioral_encode and market_encoder.

#importing libraries

import duckdb
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os


def plotting_graphs():
    print("Generating graphs using cleaned ACS and Optiver datasets.")
    
    # Loading cleaned datasets from output directory

    
    parquet_path = "../outcomes/parquet/cleaned_optiver_data.parquet"
    micro_path = "../outcomes/parquet/micro_data.parquet"
    csv_path = "../outcomes/csv/cleaned_acs_data.csv"

    if not os.path.exists(parquet_path):
        print("Error: Cleaned Optiver dataset not found.")
        return

    if not os.path.exists(micro_path):
        print("Error: Microstructure feature dataset not found.")
        return

    if not os.path.exists(csv_path):
        print("Error: Cleaned ACS dataset not found.")
        return

    # Recovering actual volatility distribution from Optiver dataset
    micro_path = "../outcomes/parquet/micro_data.parquet"
    con_q = duckdb.connect(database=':memory:')
    con_q.execute("SET threads = 2")
    con_q.execute("SET preserve_insertion_order = false")
    print("Estimating volatilty percentiles from sample dataset of 500000")
    q_df = con_q.execute(f"""
        SELECT 
            quantile_cont(rolling_volatility, 0.10) as p10,
            quantile_cont(rolling_volatility, 0.25) as p25,
            quantile_cont(rolling_volatility, 0.50) as p50,
            quantile_cont(rolling_volatility, 0.75) as p75,
            quantile_cont(rolling_volatility, 0.90) as p90,
            quantile_cont(rolling_volatility, 0.95) as p95,
            quantile_cont(rolling_volatility, 0.99) as p99,
            quantile_cont(rolling_volatility, 0.50) as median_v
        FROM read_parquet('{micro_path}') 
        WHERE rolling_volatility IS NOT NULL
        USING SAMPLE reservoir (500000 ROWS) REPEATABLE (42)
    """).fetchdf()
    con_q.close()

    if q_df.empty:
        print("Error: Could not compute volatility quantiles.")
        return

    vol_percentiles = [q_df['p10'].iloc[0], q_df['p25'].iloc[0], q_df['p50'].iloc[0], 
                       q_df['p75'].iloc[0], q_df['p90'].iloc[0], q_df['p95'].iloc[0], q_df['p99'].iloc[0]]
    median_vol = q_df['median_v'].iloc[0]

    print("Volatility percentiles calculated")
    
    os.makedirs("../outcomes/graphs", exist_ok=True)
    os.makedirs("../outcomes", exist_ok=True)
    sns.set_style("whitegrid")

    # Stream ACS in chunks to compute behavioral scores across full population

    chunk_size = 500000
    all_biases = []
    all_ages = []
    
    print(f"Streaming and processing datasets in chunks of {chunk_size:,}")
    for chunk in pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False):
        if 'bias_score' not in chunk.columns: 
            from behavioral_encode import calculate_bias
            chunk['bias_score'] = chunk['AGEP'].apply(calculate_bias)
        biases = chunk['bias_score'].values
        ages = chunk['AGEP'].values if 'AGEP' in chunk.columns else np.zeros(len(chunk))
        
        all_biases.extend(biases)
        all_ages.extend(ages)
        
    plot_df = pd.DataFrame({
        'User_Bias': all_biases,
        'User_Age': all_ages
    })
    
    # Define multiplier function m(B_i) matching architectural guidelines

    def get_multiplier(b):
        if b > 0.4:
            return 1.5
        elif b < -0.4:
            return 0.8
        else:
            return 1.0

    plot_df['Multiplier'] = plot_df['User_Bias'].apply(get_multiplier)
    
    # Use median observed market volatility for baseline cross-sectional mapping

    median_vol = q_df['median_v'].values[0]
    plot_df['Sample_Hedge_Ratio'] = plot_df['Multiplier'] * median_vol * 100

    # 1. Bias Distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(data=plot_df, x='User_Bias', bins=30, kde=True, color='teal')
    plt.axvline(0.4, color='crimson', linestyle='--', linewidth=2, label='Overconfidence Threshold (>0.4)')
    plt.axvline(-0.4, color='darkorange', linestyle='--', linewidth=2, label='Frugality Threshold (<-0.4)')
    plt.title("Distribution of Model-Implied Behavioral Scores ($B_i$)", fontsize=14, fontweight='bold')
    plt.xlabel("Behavioral Bias Score ($B_i$)", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig("../outcomes/graphs/bias_distribution.png", dpi=300)
    plt.close()
    print(" -> Saved bias_distribution.png")

    # 2. Bias Score vs. Hedge Ratio 

    plt.figure(figsize=(12, 6))
    scatter_subset = plot_df.sample(n=min(5000, len(plot_df)), random_state=42)
    
    conditions = [
        scatter_subset['User_Bias'] > 0.4,
        scatter_subset['User_Bias'] < -0.4
    ]
    choices = ['Overconfidence (>0.4)', 'Frugality (<-0.4)']
    scatter_subset['Behavioral_Regime'] = np.select(conditions, choices, default='Neutral (-0.4 to 0.4)')
    
    sns.scatterplot(
        data=scatter_subset, 
        x='User_Bias', 
        y='Sample_Hedge_Ratio', 
        hue='Behavioral_Regime',
        palette={'Overconfidence (>0.4)': 'crimson', 'Neutral (-0.4 to 0.4)': 'royalblue', 'Frugality (<-0.4)': 'darkorange'},
        alpha=0.6,
        s=50
    )
    plt.axvline(0.4, color='gray', linestyle=':')
    plt.axvline(-0.4, color='gray', linestyle=':')
    plt.title("Contract Architecture: Behavioral Bias ($B_i$) vs. Personalized Hedge Ratio ($H_i$)", fontsize=14, fontweight='bold')
    plt.xlabel("Behavioral Bias Score ($B_i$)", fontsize=12)
    plt.ylabel("Hedge Ratio (%)", fontsize=12)
    plt.legend(title="Behavioral Regime", loc='upper left')
    plt.tight_layout()
    plt.savefig("../outcomes/graphs/bias_vs_hedge_ratio.png", dpi=300)
    plt.close()
    print(" -> Saved bias_vs_hedge_ratio.png")

    # 3. Personalized Hedge Ratio vs. Market Volatility

    plt.figure(figsize=(10, 6))
    test_biases = {
        'Low Bias (Frugal, $b = -0.6$)': -0.6, 
        'Neutral Bias ($b = 0.0$)': 0.0, 
        'High Bias (Overconfident, $b = 0.6$)': 0.6
    }
    
    # Use volatility range

    actual_vols = np.linspace(q_df['p10'].values[0], q_df['p99'].values[0], 100)

    for label, b_val in test_biases.items():
        mult = get_multiplier(b_val)
        hedges = actual_vols * mult * 100
        plt.plot(actual_vols, hedges, linewidth=2.5, label=label)

    plt.title(r"Hedge Ratio vs. Observed Market Volatility ($\sigma_t$)", fontsize=14, fontweight='bold')
    plt.xlabel(r"Observed Market Volatility ($\sigma_t$)", fontsize=12)
    plt.ylabel("Hedge Ratio (%)", fontsize=12)
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig("../outcomes/graphs/personalized_hedge_vs_volatility.png", dpi=300)
    plt.close()
    print(" -> Saved personalized_hedge_vs_volatility.png")

    # 4: Heatmap Matrix 

    bias_range = np.linspace(-1, 1, 30)
    vol_percentiles = [q_df['p10'].values[0], q_df['p25'].values[0], q_df['p50'].values[0], 
                   q_df['p75'].values[0], q_df['p90'].values[0], q_df['p95'].values[0], q_df['p99'].values[0]]
    x_labels = [f"P{p} ({v:.4f})" for p, v in zip([10, 25, 50, 75, 90, 95, 99], vol_percentiles)]

    matrix_data = []
    for b in bias_range:
        row = []
        mult = get_multiplier(b)
        for v in vol_percentiles:
            hedge = (v * mult) * 100
            row.append(hedge)
        matrix_data.append(row)

    plt.figure(figsize=(11, 8))
    sns.heatmap(
        matrix_data, 
        xticklabels=x_labels, 
        yticklabels=np.round(bias_range, 2),
        cmap="YlOrRd",
        annot=False,
        cbar_kws={'label': 'Hedge Ratio (%)'}
    )
    plt.title(r"Architect Matching Matrix: Optiver Volatility Percentiles $\times$ Behavioral Bias", fontsize=14, fontweight='bold')
    plt.xlabel(r"Observed Market Volatility Percentile ($\sigma_t$)", fontsize=12)
    plt.ylabel("Model-Implied Behavioral Score ($B_i$)", fontsize=12)
    plt.tight_layout()
    plt.savefig("../outcomes/graphs/matching_matrix.png", dpi=300)
    plt.close()
    print(" -> Saved matching_matrix.png")

    print("All graphs successfully generated and saved!")

if __name__ == "__main__":
    plotting_graphs()