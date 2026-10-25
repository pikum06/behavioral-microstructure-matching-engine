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

def load_cleaned_behavioral_profiles(file_path="../outcomes/csv/cleaned_behavioral_profiles.csv", chunk_size=500000):
    """
    Loads the fully cleaned ACS behavioral profiles dataset in memory-safe chunks.
    """
    if not os.path.exists(file_path):
        print(f"Error: Cleaned ACS file not found at {file_path}. Run cleaning pipeline first.")
        return None
    
    print(f"Loading cleaned ACS behavioral profiles in chunks of {chunk_size:,}...")
    chunks = []
    for chunk in pd.read_csv(file_path, chunksize=chunk_size, low_memory=False):
        chunks.append(chunk)
    
    df = pd.concat(chunks, ignore_index=True)
    print(f"Loaded {len(df):,} total cleaned behavioral profiles successfully.")
    return df

if __name__ == "__main__":
    ACS_CLEAN_PATH = "../outcomes/csv/cleaned_behavioral_profiles.csv"
    profiles = load_cleaned_behavioral_profiles(ACS_CLEAN_PATH)
    if profiles is not None:
        print(" BEHAVIORAL PROFILES LOADED SUCCESSFULLY ")
        print(f"Total Profiles: {len(profiles):,}")
        print(profiles[['AGEP', 'PINCP', 'bias_score']].head())