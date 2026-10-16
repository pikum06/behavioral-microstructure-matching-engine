import pandas as pd
import numpy as np
import os

def calc_wap(df):
    "Calculates Weighted Average Price (Micro-Perspective)"
    # Using 'bid_price1' and 'ask_price1' from Optiver book data
    wap = (df['bid_price1'] * df['ask_size1'] + df['ask_price1'] * df['bid_size1']) / (df['bid_size1'] + df['ask_size1'])
    return wap

def calc_order_flow_imbalance(df):
    "Measures the 'Net Buying Pressure'. Key variable' Information-Theoretic approach."
    return (df['bid_size1'] - df['ask_size1']) / (df['bid_size1'] + df['ask_size1'])

def process_microstructure_data(file_path):
    if not os.path.exists(file_path):
        print(f"Error: Path {file_path} not found.")
        return None
    
    # Load local parquet
    df = pd.read_parquet(file_path).head(1000)
    
    # Feature Engineering
    df['wap'] = calc_wap(df)


    # Calculate log returns per time_id
    df['log_return'] = df.groupby('time_id')['wap'].transform(lambda x: np.log(x).diff())


    # Order Flow Imbalance (Microstructure Signal)
    df['ofi'] = calc_order_flow_imbalance(df)

    
    # Aggregating to the 'Market State' level
    features = df.groupby('time_id').agg({
        'log_return': lambda x: np.sqrt(np.sum(x**2)),
        'ofi': 'mean',
        'bid_size1': 'mean',
        'ask_size1': 'mean'
    }).reset_index()

    # Rename columns for clarity
    features.columns = ['time_id', 'realized_vol', 'avg_ofi', 'mean_bid_size', 'mean_ask_size']
    features['liquidity_depth'] = features['mean_bid_size'] + features['mean_ask_size']
    
    return features
# Local Test Execution
if __name__ == "__main__":
    LOCAL_PATH = "../data/optiver/book_train.parquet"
    test_file = os.path.join(LOCAL_PATH, "stock_id=0")
    if os.path.exists(test_file):
        micro_signals = process_microstructure_data(test_file)
        print("Microstructure signals generated successfully!")
        print(micro_signals.head())
    else:
        print(f"Please ensure data is in: {test_file}")