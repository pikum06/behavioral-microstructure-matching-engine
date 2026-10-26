#Verifies feature extraction and contract architecture from behaviroal_encode and contract_architect

import os
import duckdb
from behavioral_encode import load_cleaned_acs_data
from contract_architect import contract_architect

def test_pipeline():
    print("Running pipeline verification tests")
    
    # 1. Verify ACS and Bias Score

    acs_path = "../outcomes/csv/cleaned_acs_data.csv"
    if os.path.exists(acs_path):
        user_df = load_cleaned_acs_data(acs_path, chunk_size=500000)
        assert user_df is not None and 'bias_score' in user_df.columns, "ACS test failed: bias_score missing"
        print(" -> ACS dataset & bias_score verification passed.")
    else:
        print("Error: Cleaned ACS CSV not found.")
        return False

    # 2. Verify Enriched Microstructure Parquet Output

    micro_path = "../outcomes/parquet/micro_data.parquet"
    if os.path.exists(micro_path):
        con = duckdb.connect(database=':memory:')

        sample_market = con.execute(f"SELECT * FROM read_parquet('{micro_path}') WHERE rolling_volatility IS NOT NULL LIMIT 1").fetchdf().iloc[0]
        con.close()
        print(" Microdata.parquet dataset verification passed.")
        
        # 3. Test Contract Architect

        sample_user = user_df.sample(1).iloc[0]
        contract = contract_architect(sample_user, sample_market)
        
        assert isinstance(contract, dict), "Contract architect failed to return a dictionary"
        print(" -> Contract architect test passed. Sample Output:")
        for k, v in contract.items():
            print(f"    {k}: {v}")
        return True
    else:
        print(f"Error: Enriched micro parquet file not found at {micro_path}.")
        return False

if __name__ == "__main__":
    test_pipeline()