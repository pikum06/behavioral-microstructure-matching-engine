#creting a behavioral encode to anlayze the "Experience Effect" by coming ACS 2015 dataset and optiver dataset 
 
#importing libraries

import pandas as pd
import numpy as np
import os
def calculate_bias(age):
    birth_year = 2015 - age

    # 1988 birth = 20 years old in 2008
    
    dist_from_crisis = abs(birth_year - 1988) 
    
    # Smooth exponential decay: Bias = Amplitude * e^(-distance/scale)
    
    smooth_bias = -0.8 * np.exp(-dist_from_crisis / 12)
    
    # If they were born earlier than 1980 
    
    if birth_year < 1980:
        smooth_bias = 0.5 * np.exp(-abs(birth_year - 1975) / 10)
        
    return round(smooth_bias, 3)

def load_cleaned_acs_data(file_path="../outcomes/csv/cleaned_acs_data.csv", chunk_size=500000):
    """
    Loads the fully cleaned ACS dataset in memory-safe chunks.
    """
    if not os.path.exists(file_path):
        print(f"Error: Cleaned ACS file not found at {file_path}. Run cleaning pipeline first.")
        return None
    
    print(f"Loading cleaned ACS dataset in chunks of {chunk_size:,}.")
    chunks = []
    for chunk in pd.read_csv(file_path, chunksize=chunk_size, low_memory=False):
        if 'AGEP' not in chunk.columns:
            print("Error: 'AGEP' column missing from ACS data.")
            return None
        chunk['AGEP'] = pd.to_numeric(chunk['AGEP'], errors='coerce')
        chunk = chunk.dropna(subset=['AGEP'])
        chunk['bias_score'] = chunk['AGEP'].apply(calculate_bias)
        chunks.append(chunk)
    
    df = pd.concat(chunks, ignore_index=True)
    print(f"Loaded {len(df):,} total cleaned ACS dataset!")
    return df

if __name__ == "__main__":
    ACS_CLEAN_PATH = "../outcomes/csv/cleaned_acs_data.csv"
    profiles = load_cleaned_acs_data(ACS_CLEAN_PATH)
    if profiles is not None:
        print(" Cleaned ACS Dataset loaded")
        print(f"Total Profiles: {len(profiles):,}")
        print(profiles[['AGEP', 'PINCP', 'bias_score']].head())