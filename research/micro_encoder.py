# micro_encoder.py
import duckdb
import pandas as pd
import os

def process_microstructure_data(file_path="../outcomes/parquet/cleaned_microstructure.parquet"):
    """
    Safely loads pre-cleaned microstructure data using DuckDB, 
    inspects columns, and standardizes them for contract architecture.
    """
    if not os.path.exists(file_path):
        alt_path = "../outcomes/parquet/cleaned_microstructure.parquet"
        if os.path.exists(alt_path):
            file_path = alt_path
        else:
            print(f"Error: Cleaned microstructure file not found at {file_path} or {alt_path}.")
            return None
    
    print(f"Loading pre-cleaned microstructure data safely via DuckDB from {file_path}...")
    
    # Query a memory-safe subset using DuckDB
    query = f"SELECT * FROM read_parquet('{file_path}') LIMIT 50000"
    df = duckdb.query(query).to_df()
    
    print(f"Available columns in parquet: {df.columns.tolist()}")
    
    # Automatically map common column name variations to what the pipeline expects
    rename_map = {}
    for col in df.columns:
        col_lower = col.lower()
        if any(term in col_lower for term in ['vol', 'volatility']) and 'realized_vol' not in df.columns:
            rename_map[col] = 'realized_vol'
        elif any(term in col_lower for term in ['ofi', 'order_flow']) and 'avg_ofi' not in df.columns:
            rename_map[col] = 'avg_ofi'
            
    if rename_map:
        df = df.rename(columns=rename_map)
        print(f"Standardized columns: {df.columns.tolist()}")
        
    # Fallback defaults if columns are completely missing to prevent crashes
    if 'realized_vol' not in df.columns:
        print("Warning: 'realized_vol' not found. Assigning default baseline volatility.")
        df['realized_vol'] = 0.005
    if 'avg_ofi' not in df.columns:
        print("Warning: 'avg_ofi' not found. Assigning default baseline OFI.")
        df['avg_ofi'] = 0.0

    print(f"Loaded {len(df):,} market state records safely into memory.")
    return df

if __name__ == "__main__":
    PARQUET_PATH = "../outcomes/parquet/cleaned_microstructure.parquet"
    micro_signals = process_microstructure_data(PARQUET_PATH)
    if micro_signals is not None:
        print("Microstructure signals loaded successfully!")
        print(micro_signals.head())
    else:
        print(f"Please ensure file exists at: {PARQUET_PATH}")