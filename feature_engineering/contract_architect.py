#creating contract architect using behvioral_encode and micro_encoder

# importing functions
# creating contract architect using behavioral_encode and micro_encoder

# importing libraries
import os
import duckdb
from behavioral_encode import load_cleaned_acs_data

def contract_architect(user, market_moment):
    """The Core Method: Matching unique life-history with high-frequency market microstructure."""
   
    bias = float(user['bias_score'])
    market_vol = float(market_moment['rolling_volatility'])
    base_risk = market_vol

    # Bias adjustments
    if bias > 0.4:
        adjustment = "high-Risk Adjustment"
        personalized_hedge = base_risk * 1.5
    elif bias < -0.4:
        adjustment = "Lower-Risk Adjustment"
        personalized_hedge = base_risk * 0.8
    else:
        adjustment = "Standard Risk Alignment"
        personalized_hedge = base_risk     

    return {
        "User_Age": user['AGEP'],
        "User_Bias": round(bias, 2),
        "Market_Vol": round(market_vol, 5),
        "Adjustment_Type": adjustment,
        "Prototype_Hedge_Score": round(personalized_hedge * 100, 2)
    }

if __name__ == "__main__":
    print("Architect initializing engines for datasets...")
    
    acs_path = "../outcomes/csv/cleaned_acs_data.csv"
    micro_path = "../outcomes/parquet/enriched_micro_data.parquet"
    
    user_df = load_cleaned_acs_data(acs_path)
    
    if user_df is not None and os.path.exists(micro_path):

        # Safely fetch a single test record using DuckDB from the persisted parquet file
        con = duckdb.connect(database=':memory:')
        sample_market = con.execute(f"SELECT * FROM read_parquet('{micro_path}') LIMIT 1").fetchdf().iloc[0]
        con.close()
        
        sample_user = user_df.sample(1).iloc[0]
        
        contract = contract_architect(sample_user, sample_market)
        print("\nPERSONALIZED FINANCIAL PRODUCT ARCHITECTURE (FULL-SCALE)")
        for key, value in contract.items():
            print(f"{key}: {value}")
    else:
        print("Error: Could not load datasets or enriched parquet file. Ensure main.py has been run.")