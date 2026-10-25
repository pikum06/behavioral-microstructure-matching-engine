# Master Orchestrator for the Full Research Pipeline

from behavioral_encode import load_cleaned_behavioral_profiles
from micro_encoder import process_microstructure_data
from contract_architect import architect_personalized_contract
from visualize_contract import generate_architect_plot

def main():
    print("Starting Master Research Pipeline Orchestrator")
    
    #Load cleaned ACS profiles using chunking
    print("\nLoading Cleaned ACS Behavioral Profiles")
    user_df = load_cleaned_behavioral_profiles("../outcomes/csv/cleaned_behavioral_profiles.csv")
    if user_df is None:
        print("Error: Cleaned ACS profile dataset not found.")
        return

    #Process Optiver microstructure data across partitions
    print("\nProcessing Optiver Microstructure Data")
    market_df = process_microstructure_data("../outcomes/parquet/cleaned_microstructure.parquet")
    if market_df is None:
        print("Error: Optiver market dataset not found.")
        return

    # Run single test architecture sample
    
    print("\nRunning Sample Contract Architecture")
    sample_market = market_df.iloc[0]
    sample_user = user_df.sample(1).iloc[0]
    contract = architect_personalized_contract(sample_user, sample_market)
    for key, value in contract.items():
        print(f"  {key}: {value}")

    # Generate all research visualizations and exhibits
    
    generate_architect_plot()
    
    print("Pipeline Execution Completed!")
    
if __name__ == "__main__":
    main()