# conducting data_analysis on the ACS data. 

# importing libraries

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os

def acs_data_analysis(file_path="../outcomes/csv/cleaned_acs_data.csv", chunk_size=500000):
    if not os.path.exists(file_path):
        alt_path = "../outcomes/csv/cleaned_acs_data.csv"
        if os.path.exists(alt_path):
            file_path = alt_path
        else:
            print(f"Error: Dataset not found at {file_path}.")
            return
        
    print("Starting ACS data analysis.")
    
    os.makedirs("../outcomes/graphs", exist_ok=True)
    sns.set_style("whitegrid")

    # Containers to accumulate chunking.
     
    age_income_chunks = []
    income_list = []
    
    # Dictionary to aggregate PINCP values per AGEP.

    age_income_map = {}

    total_rows = 0
    for chunk_idx, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size, low_memory=False)):
        clean_chunk = chunk[['AGEP', 'PINCP']].dropna()
        total_rows += len(clean_chunk)
        
        # Accumulate raw income array for global distribution & Lorenz curve

        income_list.append(clean_chunk['PINCP'].values)
        
        # Accumulate for hexbin plotting 

        age_income_chunks.append(clean_chunk.sample(n=min(100000, len(clean_chunk)), random_state=42))
        
        # Group by age to merge exact percentiles/medians across chunks

        grouped = clean_chunk.groupby('AGEP')['PINCP']
        for age, group in grouped:
            if age not in age_income_map:
                age_income_map[age] = []
            age_income_map[age].extend(group.values)
            
        print(f"Processed chunk {chunk_idx + 1} ({total_rows:,} total rows evaluated)...")

    # Combine dataframes for hexbin

    plot_df = pd.concat(age_income_chunks, ignore_index=True)
    full_income = np.concatenate(income_list)

    # Compute exact statistics

    age_stats = []
    for age, incomes in sorted(age_income_map.items()):
        inc_arr = np.array(incomes)
        age_stats.append({
            'AGEP': age,
            'P25': np.percentile(inc_arr, 25),
            'P50': np.median(inc_arr),
            'P75': np.percentile(inc_arr, 75)
        })
    stats_df = pd.DataFrame(age_stats)

    print(f"Population analysis complete. Total valid records: {total_rows:,}")

    # 1. Age vs Income Joint Density (Hexbin)

    plt.figure(figsize=(10, 6))
    plt.hexbin(plot_df['AGEP'], plot_df['PINCP'], gridsize=40, cmap='Blues', mincnt=1)
    plt.colorbar(label='Observation Density')
    plt.title("Joint Distribution: Age vs. Income", fontsize=14, fontweight='bold')
    plt.xlabel("User Age (Years)", fontsize=12)
    plt.ylabel("Income ($)", fontsize=12)
    plt.tight_layout()
    plt.savefig("../outcomes/graphs/income_age_density.png", dpi=300)
    plt.close()
    print(" -> Saved income_age_density.png")

    # 2. Median Income by Age

    plt.figure(figsize=(10, 6))
    sns.lineplot(data=stats_df, x='AGEP', y='P50', color='royalblue', linewidth=2.5)
    plt.title("Median Income by Age", fontsize=14, fontweight='bold')
    plt.xlabel("User Age (Years)", fontsize=12)
    plt.ylabel("Median Income ($)", fontsize=12)
    plt.tight_layout()
    plt.savefig("../outcomes/graphs/median_income_by_age.png", dpi=300)
    plt.close()
    print(" -> Saved median_income_by_age.png")

    # 3. Income Percentiles by Age

    plt.figure(figsize=(10, 6))
    plt.plot(stats_df['AGEP'], stats_df['P50'], label='Median (P50)', color='darkblue', linewidth=2)
    plt.plot(stats_df['AGEP'], stats_df['P75'], label='75th Percentile (P75)', color='teal', linestyle='--', linewidth=1.5)
    plt.plot(stats_df['AGEP'], stats_df['P25'], label='25th Percentile (P25)', color='orange', linestyle='--', linewidth=1.5)
    plt.fill_between(stats_df['AGEP'], stats_df['P25'], stats_df['P75'], color='teal', alpha=0.1, label='IQR (P25-P75)')
    plt.title("Income Percentiles by Age", fontsize=14, fontweight='bold')
    plt.xlabel("User Age (Years)", fontsize=12)
    plt.ylabel("Income ($)", fontsize=12)
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig("../outcomes/graphs/income_percentiles_by_age.png", dpi=300)
    plt.close()
    print(" -> Saved income_percentiles_by_age.png")

    # 4. Income Distribution

    plt.figure(figsize=(10, 6))
    sns.histplot(full_income, bins=50, kde=True, color='purple')
    plt.title("Income Distribution", fontsize=14, fontweight='bold')
    plt.xlabel("Income ($)", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.tight_layout()
    plt.savefig("../outcomes/graphs/income_distribution.png", dpi=300)
    plt.close()
    print(" -> Saved income_distribution.png")

    # 5. Lorenz Curve & Gini Coefficient

    plt.figure(figsize=(10, 6))
    valid_income = full_income[full_income >= 0]
    valid_income = np.sort(valid_income)
    
    n = len(valid_income)
    if n > 0:
        cum_income = np.cumsum(valid_income)
        total_income = cum_income[-1]
        
        if total_income > 0:
            lorenz_x = np.linspace(0.0, 1.0, n + 1)
            lorenz_y = np.insert(cum_income / total_income, 0, 0)
            
            b = np.trapezoid(lorenz_y, lorenz_x)
            gini = 1 - 2 * b
            
            plt.plot(lorenz_x, lorenz_y, label=f'Lorenz Curve (Gini = {gini:.4f})', color='darkgreen', linewidth=2)
            plt.plot([0, 1], [0, 1], label='Line of Equality', color='navy', linestyle='--', linewidth=1.5)
            plt.fill_between(lorenz_x, lorenz_y, lorenz_x, color='green', alpha=0.1)
            
            plt.title("Lorenz Curve & Income Inequality", fontsize=14, fontweight='bold')
            plt.xlabel("Cumulative Share of Population", fontsize=12)
            plt.ylabel("Cumulative Share of Income", fontsize=12)
            plt.legend(loc='upper left')
            plt.tight_layout()
            plt.savefig("../outcomes/graphs/lorenz_curve.png", dpi=300)
            plt.close()
            print(f" -> Saved lorenz_curve.png (Calculated Gini Coefficient: {gini:.4f})")
    
    print("Data analysis for ACS data completed!")

if __name__ == "__main__":
    acs_data_analysis()