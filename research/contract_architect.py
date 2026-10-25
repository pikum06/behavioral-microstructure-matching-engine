from micro_encoder import process_microstructure_data
from behavioral_encode import load_cleaned_behavioral_profiles


def architect_personalized_contract(user, market_moment):
    """The Core Method: Matching unique life-history with high-frequency market microstructure."""
    bias = user['bias_score']
    market_vol = market_moment['realized_vol']

    # Order Flow Imbalance
    
    ofi = market_moment['avg_ofi'] 

    # Determining Base Risk (Market Reality)

    base_risk = market_vol * (1 + abs(ofi))

    # Bias adjustments

    if bias > 0.4:
        adjustment = "Mandatory Overconfidence Buffer"
        personalized_hedge = base_risk * 1.5
    elif bias < -0.4:
        adjustment = "Frugality Efficiency Optimization"
        personalized_hedge = base_risk * 0.8
    else:
        adjustment = "Standard Risk Alignment"
        personalized_hedge = base_risk     

    return {
        "User_Age": user['AGEP'],
        "User_Bias": round(bias, 2),
        "Market_Vol": round(market_vol, 5),
        "Adjustment_Type": adjustment,
        "Final_Hedge_Ratio": round(personalized_hedge * 100, 2)
    }

if __name__ == "__main__":
    print("Architect initializing engines for full-scale datasets")
    
    market_df = process_microstructure_data("../outcomes/parquet/cleaned_microstructure.parquet")
    user_df = load_cleaned_behavioral_profiles("../outcomes/csv/cleaned_behavioral_profiles.csv")

    if market_df is not None and user_df is not None:
        sample_market = market_df.iloc[0]
        sample_user = user_df.sample(1).iloc[0]
        
        contract = architect_personalized_contract(sample_user, sample_market)
        print("\nPERSONALIZED FINANCIAL PRODUCT ARCHITECTURE (FULL-SCALE)")
        for key, value in contract.items():
            print(f"{key}: {value}")
    else:
        print("Error: Could not load full datasets. Verify data paths.")