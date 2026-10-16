import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
#importing libraries and modules for data processing and contract architecture
import pandas as pd
import numpy as np
from micro_encoder import process_microstructure_data
from behavioral_encode import process_behavioral_profiles
#defining the method to architect personalized financial contracts based on user bias and market conditions
def architect_personalized_contract(user, market_moment):
    "The Core Method: Matching unique life-history with high-frequency market microstructure."
    bias = user['bias_score']
    market_vol = market_moment['realized_vol']
    ofi = market_moment['avg_ofi'] # Order Flow Imbalance
    #Determining Base Risk (Market Reality)
    # Volatility + aggressive order flow imbalance increases risk
    base_risk = market_vol * (1 + abs(ofi))
    # If user has an Overconfidence bias, we 'Force' a higher hedge.
    # If user has a Frugality bias, we 'Optimize' for lower cost.
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
    print("Architect initializing engines")
    market_df = process_microstructure_data("../data/optiver/book_train.parquet/stock_id=0")
    user_df = process_behavioral_profiles("../data/american_consumer_survey/ss15pusb/ss15pusb.csv")
    # picking one 'Moment in Time' and one 'User Profile'
    sample_market = market_df.iloc[0]
    sample_user = user_df.sample(1).iloc[0]
    contract = architect_personalized_contract(sample_user, sample_market)
    print("\nPERSONALIZED FINANCIAL PRODUCT ARCHITECTURE")
    for key, value in contract.items():
        print(f"{key}: {value}")