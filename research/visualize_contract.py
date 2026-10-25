# Generates research visualizations across the full 1.5 million row dataset

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os
from contract_architect import architect_personalized_contract
from micro_encoder import process_microstructure_data

def generate_architect_plot():
    print("Generating full-scale data across all 1.5 million rows using chunking.")
    
    # Load cleaned microstructure data from DuckDB parquet output
    market_df = process_microstructure_data("../outcomes/parquet/cleaned_microstructure.parquet")
    csv_path = "../outcomes/csv/cleaned_behavioral_profiles.csv"
    
    if market_df is None or not os.path.exists(csv_path):
        print("Error: Missing dataset inputs for visualization.")
        return

    sample_market = market_df.iloc[0]
    
    # Process the full 1.5M rows in memory-safe chunks of 500,000
    chunk_size = 500000
    all_biases = []
    all_ages = []
    all_hedge_ratios = []
    all_adjustments = []
    
    print(f"Streaming and processing full ACS dataset in chunks of {chunk_size:,}...")
    for chunk in pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False):
        for _, user in chunk.iterrows():
            contract = architect_personalized_contract(user, sample_market)
            all_biases.append(contract['User_Bias'])
            all_ages.append(contract['User_Age'])
            all_hedge_ratios.append(contract['Final_Hedge_Ratio'])
            all_adjustments.append(contract['Adjustment_Type'])
            
    # Combine into a unified DataFrame representing the full population
    plot_df = pd.DataFrame({
        'User_Bias': all_biases,
        'User_Age': all_ages,
        'Final_Hedge_Ratio': all_hedge_ratios,
        'Adjustment_Type': all_adjustments
    })
    
    print(f"Successfully processed all {len(plot_df):,} rows across the full population.")

    os.makedirs("../outcomes/graphs", exist_ok=True)
    os.makedirs("../outcomes", exist_ok=True)
    
  
    # 1. Subplot Figure: Bias Distribution & Market Volatility Sensitivity
  
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(16, 6))
    
    sns.histplot(data=plot_df, x='User_Bias', bins=15, ax=axes[0], kde=True, color='teal')
    axes[0].set_title("Distribution of Behavioral Bias in ACS Population")
    axes[0].set_xlabel("Bias Score")

    market_sim = []
    vols = np.linspace(0.001, 0.01, 50) 
    biases = plot_df['User_Bias'].values
    
    multipliers = np.where(biases > 0.4, 1.5, 
                  np.where(biases < -0.4, 0.8, 1.0))
    
    for v in vols:
        all_hedges = (v * multipliers) * 100
        market_sim.append({
            'Volatility': v,
            'Average_Hedge': np.mean(all_hedges),
            'Max_Hedge': np.max(all_hedges),
            'Min_Hedge': np.min(all_hedges)
        })
    
    sim_df = pd.DataFrame(market_sim)
    
    sns.lineplot(data=sim_df, x='Volatility', y='Average_Hedge', ax=axes[1], color='red', label='Population Average')
    axes[1].fill_between(sim_df['Volatility'], sim_df['Min_Hedge'], sim_df['Max_Hedge'], color='red', alpha=0.2, label='Population Range')

    axes[1].set_title("Contract Sensitivity to Market Micro-Volatility")
    axes[1].set_xlabel("Realized Volatility")
    axes[1].set_ylabel("Hedge Ratio (%)")
    axes[1].legend(loc='upper left')
    
    plt.tight_layout()
    plt.savefig("../outcomes/graphs/architect_research_exhibit3.png")
    print("Research Exhibit saved to ../outcomes/graphs/architect_research_exhibit3.png")
    plt.close()

    # 2. Scatter Plot: Age vs Hedge Ratio
    
    plt.figure(figsize=(12, 6))
    sns.set_style("whitegrid")
    
    scatter_subset = plot_df.sample(n=min(3000, len(plot_df)), random_state=42)
    sns.scatterplot(
        data=scatter_subset, 
        x='User_Age', 
        y='Final_Hedge_Ratio', 
        hue='Adjustment_Type',
        palette='viridis',
        s=100
    )
    
    plt.title("The Architect: Personalized Hedge Ratios based on Life-History Bias", fontsize=15)
    plt.xlabel("User Age (Years)", fontsize=12)
    plt.ylabel("Hedge Ratio (Protection Level %)", fontsize=12)
    plt.legend(title="Behavioral Correction", bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig("../outcomes/graphs/architect_results3.png")
    print("Visualization saved to ../outcomes/graphs/architect_results3.png")
    plt.close()


    # 3. Pie Chart for Behavioral Adjustment Proportions

    plt.figure(figsize=(9, 9))
    adjustment_counts = plot_df['Adjustment_Type'].value_counts()
    
    plt.pie(
        adjustment_counts, 
        labels=adjustment_counts.index, 
        autopct='%1.1f%%', 
        startangle=140, 
        colors=sns.color_palette("Set2"),
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}
    )
    plt.title("Proportion of Behavioral Adjustments Across Population", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig("../outcomes/graphs/adjustment_type_pie.png")
    print("Pie chart saved to ../outcomes/graphs/adjustment_type_pie.png")
    plt.close()


    # 4. Heatmap Matrix: Micro-Volatility vs Behavioral Bias

    bias_range = np.linspace(-1, 1, 20)
    vol_range = np.linspace(0.001, 0.01, 20)
    
    matrix_data = []
    for b in bias_range:
        row = []
        for v in vol_range:
            multiplier = 1.5 if b > 0.4 else (0.8 if b < -0.4 else 1.0)
            hedge = (v * multiplier) * 100
            row.append(hedge)
        matrix_data.append(row)

    plt.figure(figsize=(10, 8))
    sns.heatmap(
        matrix_data, 
        xticklabels=np.round(vol_range, 4), 
        yticklabels=np.round(bias_range, 2),
        cmap="YlOrRd",
        annot=False
    )
    plt.title("The Architect Matching Matrix: Hedge Ratio (%)")
    plt.xlabel("Market Micro-Volatility")
    plt.ylabel("User Behavioral Bias")
    
    plt.savefig("../outcomes/graphs/matching_matrix3.png")
    print("Matching Matrix Heatmap saved to ../outcomes/graphs/matching_matrix3.png")
    plt.close()

if __name__ == "__main__":
    generate_architect_plot()