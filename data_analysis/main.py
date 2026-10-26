# Main Pipeline for data analysis orchestrator

from data_analysis_acs import acs_data_analysis
from data_analysis_parquet import parquet_data_analysis

def main():
    
    print("Starting Dataset Analysis Pipeline")
    
    
    # Run pure EDA on Cleaned ACS Behavioral Profiles

    print("\nAnalyzing Cleaned ACS Dataset")
    acs_data_analysis()

    # Step 2: Run pure EDA on Cleaned Microstructure Parquet Data

    print("\nAnalyzing Cleaned Optiver Parquet Data")
    parquet_data_analysis()
    
  
    print("Dataset Analysis Pipeline Completed!")
    

if __name__ == "__main__":
    main()