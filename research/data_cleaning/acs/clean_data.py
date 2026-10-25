# clean_data_acs.py
import pandas as pd
import numpy as np

from keras.models import load_model
import json
import sys
import os

# Import the bias function from your behavioral module instead of redefining it
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from behavioral_encode import calculate_bias

def clean_chunk_with_frozen_model(chunk, autoencoder, mean_val, std_val, numeric_cols):
    chunk['AGEP'] = pd.to_numeric(chunk['AGEP'], errors='coerce')
    chunk['PINCP'] = pd.to_numeric(chunk['PINCP'], errors='coerce')
    
    chunk['AGEP'] = chunk['AGEP'].fillna(mean_val[0])
    chunk['PINCP'] = chunk['PINCP'].fillna(mean_val[1])
    
    chunk = chunk.drop_duplicates()
    if len(chunk) < 10:
        return chunk

    data_matrix = chunk[numeric_cols].values
    normalized_data = (data_matrix - mean_val) / std_val

    # Inference & Reconstruction Error calculation

    reconstructions = autoencoder.predict(normalized_data, verbose=0)
    mse_per_row = np.mean(np.square(normalized_data - reconstructions), axis=1)

    # Filter out top 2% structural anomalies

    threshold = np.percentile(mse_per_row, 98)
    valid_indices = mse_per_row <= threshold

    cleaned_chunk = chunk.iloc[valid_indices].copy().reset_index(drop=True)
    
    # Apply imported behavioral bias calculation

    cleaned_chunk['bias_score'] = cleaned_chunk['AGEP'].apply(calculate_bias)
    
    return cleaned_chunk

def run_cleaning_pipeline(input_path, output_path, model_dir="../../../outcomes/models", chunk_size=500000):
    if not os.path.exists(input_path):
        print(f"Error: ACS file not found at {input_path}")
        return

    model_path = os.path.join(model_dir, "global_behavioral_autoencoder.h5")
    params_path = os.path.join(model_dir, "behavioral_norm_params.npz")
    cols_path = os.path.join(model_dir, "behavioral_cols.json")

    if not os.path.exists(model_path) or not os.path.exists(params_path):
        print("Error: Behavioral model files not found. Run global_model.py first!")
        return

    print("Loading frozen behavioral model and parameters")
    frozen_model = load_model(model_path)
    params = np.load(params_path)
    mean_val = params["mean"]
    std_val = params["std"]
    
    with open(cols_path, "r") as f:
        numeric_cols = json.load(f)

    cols = ['SERIALNO', 'AGEP', 'PINCP']
    print(f"Starting attribute-specific inference cleaning pipeline across chunks")
    cleaned_chunks = []

    for chunk in pd.read_csv(input_path, usecols=cols, chunksize=chunk_size, low_memory=False):
        cleaned_chunk = clean_chunk_with_frozen_model(chunk, frozen_model, mean_val, std_val, numeric_cols)
        cleaned_chunks.append(cleaned_chunk)

    print("Concatenating cleaned chunks into final output DataFrame...")
    final_df = pd.concat(cleaned_chunks, ignore_index=True)
    final_df = final_df.drop_duplicates().reset_index(drop=True)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_df.to_csv(output_path, index=False)
    print(f"Single cleaned behavioral CSV successfully saved ({len(final_df):,} rows) -> {output_path}")

if __name__ == "__main__":
    ACS_INPUT = "../../../data/american_consumer_survey/ss15pusb/ss15pusb.csv"
    ACS_OUTPUT = "../../../outcomes/csv/cleaned_behavioral_profiles.csv"
    run_cleaning_pipeline(ACS_INPUT, ACS_OUTPUT)