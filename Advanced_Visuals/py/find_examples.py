import pandas as pd
import os

# Define Path
RFEI_PATH = "../../Contra_Costa/csv/modified-retail-food-environment-index-data.xlsx - modified-retail-food-environment-index-data.xlsx.csv"

def find_examples():
    if not os.path.exists(RFEI_PATH):
        print(f"File not found: {RFEI_PATH}")
        return

    df = pd.read_csv(RFEI_PATH)
    
    # Filter for Contra Costa
    cc_df = df[(df['county_name'] == 'Contra Costa') & (df['geotype'] == 'CT')].copy()
    
    # Calculate Metrics
    cc_df['Healthy_Ratio'] = cc_df.apply(lambda row: row['numerator'] / row['denominator'] if row['denominator'] > 0 else 0, axis=1)
    
    # 1. FIND SWAMPS (The "Red" Examples)
    # Criteria: High Denominator (>10), Low Ratio (<0.1)
    swamps = cc_df[(cc_df['denominator'] > 10) & (cc_df['Healthy_Ratio'] < 0.15)].sort_values('denominator', ascending=False)
    
    print("\n=== TOP 5 FOOD SWAMPS (Red Examples) ===")
    print("Criteria: Lots of stores, but almost no healthy ones.")
    print(swamps[['geoname', 'numerator', 'denominator', 'Healthy_Ratio']].head(5))

    # 2. FIND OASIS (The "Green" Examples)
    # Criteria: High Ratio (>0.5), Decent Denominator (>3)
    greens = cc_df[(cc_df['denominator'] > 3) & (cc_df['Healthy_Ratio'] > 0.4)].sort_values('Healthy_Ratio', ascending=False)
    
    print("\n=== TOP 5 HEALTHY OASES (Green Examples) ===")
    print("Criteria: High % of healthy stores.")
    print(greens[['geoname', 'numerator', 'denominator', 'Healthy_Ratio']].head(5))

if __name__ == "__main__":
    find_examples()
