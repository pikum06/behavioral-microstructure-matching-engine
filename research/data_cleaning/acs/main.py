# Master Orchestrator for Behavioral Attribute Pipeline

from global_model import train_global_model
from clean_data import run_cleaning_pipeline

def main():

    print("Starting Behavioral Attribute Pipeline Orchestrator")
    
    ACS_INPUT = "../../../data/american_consumer_survey/ss15pusb/ss15pusb.csv"
    ACS_OUTPUT = "../../../outcomes/csv/cleaned_behavioral_profiles.csv"
    MODEL_DIR = "../../../outcomes/models"
    
    # Train global attribute model on 500k random sample
    print("\nBehavioral Model Training & Freezing")
    success = train_global_model(
        ACS_INPUT, 
        model_dir=MODEL_DIR, 
        target_sample_size=500000, 
        chunk_size=100000
    )
    
    if not success:
        print("Pipeline stopped due to missing input file.")
        return

    # Run inference cleaning and generate single CSV with bias scores
    print("\nAttribute-Specific Inference & Cleaning")
    run_cleaning_pipeline(
        ACS_INPUT, 
        ACS_OUTPUT, 
        model_dir=MODEL_DIR, 
        chunk_size=500000
    )
    
    print("Pipeline Execution Complete!")
    print(f"Unified Clean CSV Ready -> {ACS_OUTPUT}")
   
if __name__ == "__main__":
    main()