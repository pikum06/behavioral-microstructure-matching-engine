# Master Orchestrator for the Full Research Pipeline

#calling functions

from micro_encoder import process_micro_encoder
from visualize_contract import plotting_graphs
from test_pipeline import test_pipeline

def main():
    print("Starting Master Research Pipeline Orchestrator")
    
    print("\nProcessing Microstructure Data & Outputting Parquet")
    success = process_micro_encoder()
    if not success:
        print("Error: Microstructure encoding failed.")
        return

    print("\nRunning System & Contract Verification Tests")
    test_passed = test_pipeline()
    if not test_passed:
        print("Error: Pipeline verification tests failed.")
        return

    print("\nGenerating Research Visualizations")
    plotting_graphs()
    
    print("\nPipeline Execution Completed!")

if __name__ == "__main__":
    main()