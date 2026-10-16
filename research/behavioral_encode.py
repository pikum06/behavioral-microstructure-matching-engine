import pandas as pd
import numpy as np
import os
def calculate_bias(age):
    birth_year = 2015 - age
    dist_from_crisis = abs(birth_year - 1988) # 1988 birth = 20 years old in 2008
    
    # Smooth exponential decay: Bias = Amplitude * e^(-distance/scale)
    smooth_bias = -0.8 * np.exp(-dist_from_crisis / 12)
    
    # If they were born earlier than 1980 
    if birth_year < 1980:
        smooth_bias = 0.5 * np.exp(-abs(birth_year - 1975) / 10)
        
    return round(smooth_bias, 3)
def process_behavioral_profiles(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None
    cols = ['AGEP', 'PINCP', 'SERIALNO'] 
    entrepreneur_list = []
    print("Reading file in chunks to prevent crash")
    # Read in chunks of 50,000 rows at a time
    chunk_size = 500000
    for chunk in pd.read_csv(file_path, usecols=cols, chunksize=chunk_size, low_memory=False):
        # Clean the chunk
        chunk['AGEP'] = pd.to_numeric(chunk['AGEP'], errors='coerce')
        chunk['PINCP'] = pd.to_numeric(chunk['PINCP'], errors='coerce')
        chunk = chunk.dropna(subset=['AGEP', 'PINCP'])
        
        # Filter for entrepreneurs
        subset = chunk[chunk['PINCP'] > 75000].copy()
        entrepreneur_list.append(subset)
        # Stop once got enough for a prototype
        current_total = sum(len(x) for x in entrepreneur_list)
        if current_total >= 100:
            print(f"Captured {current_total} users. Stopping for stability.")
            break
    df = pd.concat(entrepreneur_list, ignore_index=True)
    df['bias_score'] = df['AGEP'].apply(calculate_bias)
    return df
if __name__ == "__main__":
    ACS_FILE = "../data/american_consumer_survey/ss15pusb/ss15pusb.csv"
    profiles = process_behavioral_profiles(ACS_FILE)
    if profiles is not None:
        print(" BEHAVIORAL PROFILES GENERATED ")
        print(f"Total Entrepreneurs Found: {len(profiles)}")
        print(profiles[['AGEP', 'PINCP', 'bias_score']].head())