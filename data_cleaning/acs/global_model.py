# Attribute-Specific Global Pre-training Pipeline for ACS Behavioral Profiles

import pandas as pd
import numpy as np
import tensorflow as tf
from keras.models import Sequential
from keras.layers import Dense
import json
import os

def autoencoder_model(input_dim):
    """
    Builds a compact Autoencoder optimized for low-dimensional behavioral attributes (AGEP, PINCP).
    """
    model = Sequential([
        Dense(8, activation='relu', input_shape=(input_dim,)),
        Dense(4, activation='relu'),  # Core Bottleneck
        Dense(8, activation='relu'),
        Dense(input_dim, activation='linear')
    ])
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.005), 
        loss='mse'
    )
    return model

def train_global_model(input_path, model_dir="../../../outcomes/models", target_sample_size=500000, chunk_size=100000):
    if not os.path.exists(input_path):
        print(f"Error: ACS file not found at {input_path}")
        return False

    cols = ['SERIALNO', 'AGEP', 'PINCP']
    print(f"Loading target behavioral attributes {cols} for 500k random sample training.")

    # Stream through chunks to collect a balanced random sample
    sampled_dfs = []
    for chunk in pd.read_csv(input_path, usecols=cols, chunksize=chunk_size, low_memory=False):
        sampled_chunk = chunk.sample(frac=0.35, random_state=42)
        sampled_dfs.append(sampled_chunk)

    df_sample = pd.concat(sampled_dfs, ignore_index=True)
    if len(df_sample) > target_sample_size:
        df_sample = df_sample.sample(n=target_sample_size, random_state=42)

    print(f"Training sample secured: {len(df_sample):,} rows.")

    # Convert to numeric safely and handle missing values
    df_sample['AGEP'] = pd.to_numeric(df_sample['AGEP'], errors='coerce')
    df_sample['PINCP'] = pd.to_numeric(df_sample['PINCP'], errors='coerce')
    
    df_sample['AGEP'] = df_sample['AGEP'].fillna(df_sample['AGEP'].mean())
    df_sample['PINCP'] = df_sample['PINCP'].fillna(df_sample['PINCP'].mean())
    
    df_sample = df_sample.drop_duplicates()

    numeric_cols = ['AGEP', 'PINCP']
    data_matrix = df_sample[numeric_cols].values
    
    mean_val = np.mean(data_matrix, axis=0)
    std_val = np.std(data_matrix, axis=0) + 1e-8
    normalized_data = (data_matrix - mean_val) / std_val

    input_dim = data_matrix.shape[1]
    autoencoder = autoencoder_model(input_dim)
    
    print("Training attribute-specific global Autoencoder (15 epochs)")
    autoencoder.fit(
        normalized_data, normalized_data, 
        epochs=15, 
        batch_size=1024, 
        shuffle=True, 
        verbose=1
    )
    
    os.makedirs(model_dir, exist_ok=True)
    autoencoder.save(os.path.join(model_dir, "global_behavioral_autoencoder.h5"))
    np.savez(os.path.join(model_dir, "behavioral_norm_params.npz"), mean=mean_val, std=std_val)
    with open(os.path.join(model_dir, "behavioral_cols.json"), "w") as f:
        json.dump(numeric_cols, f)
        
    print(f"Behavioral global model and parameters successfully saved to '{model_dir}/'")
    return True

if __name__ == "__main__":
    ACS_INPUT = "../../../data/american_consumer_survey/ss15pusb/ss15pusb.csv"
    train_global_model(ACS_INPUT)