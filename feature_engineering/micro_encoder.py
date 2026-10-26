# using cleaned optiver dataset to build a micro_encoder and persist to parquet

import duckdb
import os

def process_micro_encoder(file_path="../outcomes/parquet/cleaned_optiver_data.parquet", 
                          output_path="../outcomes/parquet/micro_data.parquet"):
    """
    Executes window calculations (WAP, Log Returns, 5-Observation Rolling Volatility)
    in DuckDB and writes the enriched dataset directly to a Parquet file.
    """
    if not os.path.exists(file_path):
        alt_path = "../outcomes/parquet/cleaned_optiver_data.parquet"
        if os.path.exists(alt_path):
            file_path = alt_path
        else:
            print(f"Error: Cleaned optiver data not found at {file_path}.")
            return False
    
    print(f"Connecting to DuckDB to process Optiver parquet dataset: {file_path}")
    con = duckdb.connect(database=':memory:')

    schema_df = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{file_path}')").fetchdf()
    columns = schema_df['column_name'].tolist()
    
    required_cols = ['stock_id', 'time_id', 'seconds_in_bucket', 'bid_price1', 'ask_price1', 'bid_size1', 'ask_size1']
    if not all(c in columns for c in required_cols):
        print(f"Error: Missing required columns in dataset. Found: {columns}")
        con.close()
        return False

    query = f"""
        WITH base_market AS (
            SELECT stock_id, time_id, seconds_in_bucket,
                   (bid_price1 * ask_size1 + ask_price1 * bid_size1) / NULLIF(bid_size1 + ask_size1, 0) AS wap
            FROM read_parquet('{file_path}')
        ),
        rets AS (
            SELECT stock_id, time_id, seconds_in_bucket, wap,
                   CASE 
                       WHEN wap > 0 AND LAG(wap) OVER (PARTITION BY stock_id, time_id ORDER BY seconds_in_bucket) > 0 
                       THEN LN(wap / LAG(wap) OVER (PARTITION BY stock_id, time_id ORDER BY seconds_in_bucket))
                       ELSE NULL 
                   END AS log_return
            FROM base_market
        ),
        vols AS (
            SELECT stock_id, time_id, seconds_in_bucket, wap, log_return,
                   STDDEV(log_return) OVER (
                       PARTITION BY stock_id, time_id 
                       ORDER BY seconds_in_bucket 
                       ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                   ) AS rolling_volatility
            FROM rets
        )
        SELECT * FROM vols
    """
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"Executing full-dataset pipeline and exporting to {output_path}.")
    
    # Export directly to Parquet via DuckDB (Zero-memory overhead)
    con.execute(f"COPY ({query}) TO '{output_path}' (FORMAT PARQUET);")
    con.close()
    
    print("Optiver dataset saved as Parquet!")
    return True

if __name__ == "__main__":
    process_micro_encoder()