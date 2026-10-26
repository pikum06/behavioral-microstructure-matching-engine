#cleaning the book.train parquet dataset

#import libraries
import duckdb
import os

def clean_microstructure_with_duckdb(input_dir, output_parquet_path):
    """
    DuckDB high-performance pipeline for cleaning stock parquet partitions:
    - Scans root book_train.parquet recursively across all stock_id subfolders.
    - Creates a temporary table with mean imputation and null/duplicate removal.
    - Exports to Parquet using standard DuckDB table COPY syntax.
    """
    if not os.path.exists(input_dir):
        print(f"Error: Microstructure directory not found at {input_dir}")
        return

    print(f"Connecting to DuckDB and scanning all stock partitions in: {input_dir}...")
    
    # Initialize DuckDB in-memory connection

    con = duckdb.connect(database=':memory:')
    con.execute("PRAGMA memory_limit='12GB';")
    con.execute("PRAGMA threads=4;")

    os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)

    print("Executing DuckDB cleaning query via temporary table creation...")

    # Create a clean table using CTEs (avoids parser errors with direct COPY queries)

    create_table_query = f"""
        CREATE TABLE cleaned_data AS 
        WITH raw_data AS (
            SELECT * FROM read_parquet('{input_dir}/**/*.parquet', hive_partitioning=true)
        ),
        column_means AS (
            SELECT 
                avg(bid_price1) as avg_bid1,
                avg(ask_price1) as avg_ask1,
                avg(bid_size1) as avg_bsize1,
                avg(ask_size1) as avg_asize1
            FROM raw_data
        )
        SELECT DISTINCT
            r.time_id,
            r.stock_id,
            r.seconds_in_bucket,
            coalesce(r.bid_price1, m.avg_bid1) as bid_price1,
            coalesce(r.ask_price1, m.avg_ask1) as ask_price1,
            coalesce(r.bid_size1, m.avg_bsize1) as bid_size1,
            coalesce(r.ask_size1, m.avg_asize1) as ask_size1
        FROM raw_data r
        CROSS JOIN column_means m
        WHERE r.time_id IS NOT NULL 
          AND r.stock_id IS NOT NULL;
    """
    con.execute(create_table_query)

    print(f"Exporting cleaned data to Parquet -> {output_parquet_path}")

# Export table to Parquet

    copy_query = f"COPY cleaned_data TO '{output_parquet_path}' (FORMAT PARQUET, COMPRESSION ZSTD);"
    con.execute(copy_query)

    print(f"All 126+ stock parquet partitions successfully cleaned and saved!")
    con.close()

if __name__ == "__main__":
    MICRO_INPUT = "../../data/optiver/book_train.parquet"
    MICRO_OUTPUT = "../../outcomes/parquet/cleaned_optiver_data.parquet"
    
    clean_microstructure_with_duckdb(MICRO_INPUT, MICRO_OUTPUT)