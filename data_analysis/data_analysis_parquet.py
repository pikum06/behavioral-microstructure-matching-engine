# conducting data_analysis on the Optiver parquet data. 

# import libraries

import matplotlib.pyplot as plt
import seaborn as sns
import duckdb
import os

def parquet_data_analysis(file_path="../outcomes/parquet/cleaned_optiver_data.parquet"):
    if not os.path.exists(file_path):
        alt_path = "../outcomes/parquet/cleaned_optiver_data.parquet"
        if os.path.exists(alt_path):
            file_path = alt_path
        else:
            print(f"Error: Dataset not found at {file_path}.")
            return
        
    print("Generating graphs for the Parquet dataset.")
    
    con = duckdb.connect(database=':memory:')
    
    # Inspect schema dynamically

    schema_df = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{file_path}')").fetchdf()
    columns = schema_df['column_name'].tolist()
    print(f"Verified columns in parquet: {columns}")

    os.makedirs("../outcomes/graphs", exist_ok=True)
    sns.set_style("whitegrid")

    has_seconds = 'seconds_in_bucket' in columns
    has_stock_time = all(c in columns for c in ['stock_id', 'time_id'])

    if not has_seconds:
        print("ERROR: seconds_in_bucket is required for chronological analysis.")
        con.close()
        return
    
    # Define time sequencing column for ordering
    
    time_seq_col = 'seconds_in_bucket' 

    # Check if raw order book columns exist for WAP derivation
    
    has_order_book = all(c in columns for c in ['bid_price1', 'ask_price1', 'bid_size1', 'ask_size1'])

    if has_order_book:
        wap_expr = """
            (bid_price1 * ask_size1 + ask_price1 * bid_size1) / NULLIF(bid_size1 + ask_size1, 0)
        """
    else:
        wap_expr = "wap" if 'wap' in columns else "NULL"

    # Build base view with explicit WAP derivation and robust row sequencing
    
    base_view_sql = f"""
        CREATE OR REPLACE VIEW base_market AS 
        SELECT *, 
               {wap_expr} AS derived_wap
        FROM read_parquet('{file_path}')
    """
    con.execute(base_view_sql)

    # 1. WAP Time Series (Single Stock & Time Bucket Trajectory)
    
    if has_stock_time:
        sample_traj = con.execute("""
            SELECT stock_id, time_id 
            FROM base_market 
            WHERE derived_wap IS NOT NULL
            LIMIT 1
        """).fetchone()
        
        if sample_traj:
            s_id, t_id = sample_traj
            wap_df = con.execute(f"""
                SELECT {time_seq_col}, derived_wap 
                FROM base_market 
                WHERE stock_id = {s_id} AND time_id = {t_id} AND derived_wap IS NOT NULL
                ORDER BY {time_seq_col}
            """).fetchdf()
            
            if not wap_df.empty:
                plt.figure(figsize=(12, 5))
                plt.plot(wap_df[time_seq_col].values, wap_df['derived_wap'].values, color='royalblue', linewidth=1.5)
                plt.title(f"WAP Time Series (Stock ID: {s_id}, Time Bucket: {t_id})", fontsize=14, fontweight='bold')
                plt.xlabel(f"Time Sequence ({time_seq_col})", fontsize=12)
                plt.ylabel("Weighted Average Price (WAP)", fontsize=12)
                plt.tight_layout()
                plt.savefig("../outcomes/graphs/wap_time_series.png", dpi=300)
                plt.close()
                print(" -> Saved wap_time_series.png")

    # 2. Return Distribution (Log returns derived from WAP)
    
    if has_stock_time:
        ret_query = f"""
            SELECT LN(derived_wap / LAG(derived_wap) OVER (
                PARTITION BY stock_id, time_id 
                ORDER BY {time_seq_col}
            )) AS log_ret
            FROM base_market
            WHERE derived_wap > 0
        """
        ret_df = con.execute(f""" SELECT log_ret FROM ({ret_query}) WHERE log_ret IS NOT NULL USING SAMPLE 100000 ROWS""").fetchdf()

        if not ret_df.empty:
            plt.figure(figsize=(10, 6))
            sns.histplot(ret_df['log_ret'].dropna(), bins=50, kde=True, color='darkorange')
            plt.title("Return Distribution", fontsize=14, fontweight='bold')
            plt.xlabel("Log Return ($r_t$)", fontsize=12)
            plt.ylabel("Frequency", fontsize=12)
            plt.tight_layout()
            plt.savefig("../outcomes/graphs/return_distribution.png", dpi=300)
            plt.close()
            print(" -> Saved return_distribution.png")

    # 3. Volatility Distribution (5-Observation Rolling Realized Volatility)
    
    if has_stock_time:
        vol_query = f"""
            WITH returns_calc AS (
                SELECT stock_id, time_id, {time_seq_col},
                       LN(derived_wap / LAG(derived_wap) OVER (
                           PARTITION BY stock_id, time_id 
                           ORDER BY {time_seq_col}
                       )) AS log_ret
                FROM base_market
                WHERE derived_wap > 0
            )
            SELECT STDDEV(log_ret) OVER (
                PARTITION BY stock_id, time_id 
                ORDER BY {time_seq_col} 
                ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
            ) AS rolling_vol 
            FROM returns_calc
        """
        vol_df = con.execute(f"SELECT rolling_vol FROM ({vol_query}) WHERE rolling_vol IS NOT NULL USING SAMPLE 100000 ROWS").fetchdf()
        
        plt.figure(figsize=(10, 6))
        sns.histplot(vol_df['rolling_vol'], bins=50, kde=True, color='crimson')
        plt.title("5-Observation Rolling Return Volatility Distribution", fontsize=14, fontweight='bold')
        plt.xlabel(r"Rolling Realized Volatility ($\sigma_t$)", fontsize=12)
        plt.ylabel("Frequency", fontsize=12)
        plt.tight_layout()
        plt.savefig("../outcomes/graphs/volatility_distribution.png", dpi=300)
        plt.close()
        print(" -> Saved volatility_distribution.png")

    # 4. Return vs Volatility Scatter Plot (Using DuckDB stratified sampling)
    
    if has_stock_time:
        scatter_query = f"""
            WITH returns_calc AS (
                SELECT stock_id, time_id, {time_seq_col},
                       LN(derived_wap / LAG(derived_wap) OVER (
                           PARTITION BY stock_id, time_id 
                           ORDER BY {time_seq_col}
                       )) AS log_ret
                FROM base_market
                WHERE derived_wap > 0
            ),
            vol_calc AS (
                SELECT log_ret AS ret,
                       STDDEV(log_ret) OVER (
                           PARTITION BY stock_id, time_id 
                           ORDER BY {time_seq_col} 
                           ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                       ) AS rolling_vol 
                FROM returns_calc
            )
            SELECT ret, rolling_vol FROM vol_calc 
            WHERE ret IS NOT NULL AND rolling_vol IS NOT NULL
            USING SAMPLE 50000 ROWS
        """
        sample_df = con.execute(scatter_query).fetchdf()
        
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=sample_df, x='ret', y='rolling_vol', alpha=0.5, color='purple')
        plt.title("Return vs. 5-Observation Rolling Volatility", fontsize=14, fontweight='bold')
        plt.xlabel("Log Return ($r_t$)", fontsize=12)
        plt.ylabel(r"Rolling Realized Volatility ($\sigma_t$)", fontsize=12)
        plt.tight_layout()
        plt.savefig("../outcomes/graphs/return_vs_volatility.png", dpi=300)
        plt.close()
        print(" -> Saved return_vs_volatility.png")

    # 5. Volatility Clustering / Time Series (Single Stock Trajectory of Rolling Volatility)
    
    if has_stock_time:
        sample_traj_vol = con.execute("SELECT stock_id, time_id FROM base_market LIMIT 1").fetchone()
        if sample_traj_vol:
            s_id, t_id = sample_traj_vol
            vol_ts_query = f"""
                WITH returns_calc AS (
                    SELECT stock_id, time_id, {time_seq_col},
                           LN(derived_wap / LAG(derived_wap) OVER (
                               PARTITION BY stock_id, time_id 
                               ORDER BY {time_seq_col}
                           )) AS log_ret
                    FROM base_market
                    WHERE derived_wap > 0
                )
                SELECT {time_seq_col},
                       STDDEV(log_ret) OVER (
                           PARTITION BY stock_id, time_id 
                           ORDER BY {time_seq_col} 
                           ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                       ) AS rolling_vol 
                FROM returns_calc 
                WHERE stock_id = {s_id} AND time_id = {t_id}
                ORDER BY {time_seq_col}
            """
            vol_ts_df = con.execute(vol_ts_query).fetchdf()
            
            if not vol_ts_df.empty:
                plt.figure(figsize=(12, 5))
                plt.plot(vol_ts_df[time_seq_col].values, vol_ts_df['rolling_vol'].values, color='teal', linewidth=1.5)
                plt.title(f"Volatility Clustering / Time Series (Stock ID: {s_id}, Time Bucket: {t_id})", fontsize=14, fontweight='bold')
                plt.xlabel(f"Time Sequence ({time_seq_col})", fontsize=12)
                plt.ylabel(r"5-Observation Rolling Volatility ($\sigma_t$)", fontsize=12)
                plt.tight_layout()
                plt.savefig("../outcomes/graphs/volatility_clustering_time_series.png", dpi=300)
                plt.close()
                print(" -> Saved volatility_clustering_time_series.png")

    # 6. Current Volatility -> Next-Period Absolute Return within same stock & time bucket ($\sigma_{t} \rightarrow |r_{t+1}|$)
    
    if has_stock_time:
        lead_query = f"""
            WITH returns_calc AS (
                SELECT stock_id, time_id, {time_seq_col},
                       LN(derived_wap / LAG(derived_wap) OVER (
                           PARTITION BY stock_id, time_id 
                           ORDER BY {time_seq_col}
                       )) AS log_ret
                FROM base_market
                WHERE derived_wap > 0
            ),
            vol_calc AS (
                SELECT stock_id, time_id, {time_seq_col}, log_ret,
                       STDDEV(log_ret) OVER (
                           PARTITION BY stock_id, time_id 
                           ORDER BY {time_seq_col} 
                           ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                       ) AS current_vol
                FROM returns_calc
            )
            SELECT current_vol,
                   ABS(LEAD(log_ret) OVER (
                       PARTITION BY stock_id, time_id 
                       ORDER BY {time_seq_col}
                   )) AS next_abs_return
            FROM vol_calc
        """
        lead_df = con.execute(f"""
            SELECT current_vol, next_abs_return 
            FROM ({lead_query}) 
            WHERE current_vol IS NOT NULL AND next_abs_return IS NOT NULL
            USING SAMPLE 50000 ROWS
        """).fetchdf()

        if not lead_df.empty:
            plt.figure(figsize=(10, 6))
            sns.scatterplot(data=lead_df, x='current_vol', y='next_abs_return', alpha=0.4, color='darkcyan')
            plt.title(r"Current Volatility vs. Next-Period Absolute Return ($\sigma_t \rightarrow |r_{t+1}|$)", fontsize=14, fontweight='bold')
            plt.xlabel(r"Current Rolling Volatility ($\sigma_t$)", fontsize=12)
            plt.ylabel(r"Next-Period Absolute Return ($|r_{t+1}|$)", fontsize=12)
            plt.tight_layout()
            plt.savefig("../outcomes/graphs/volatility_vs_next_return.png", dpi=300)
            plt.close()
            print(" -> Saved volatility_vs_next_return.png")

    con.close()
    print("Data analysis for parquet data completed!")

if __name__ == "__main__":
    parquet_data_analysis()