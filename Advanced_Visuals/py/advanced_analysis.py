"""
=============================================================================
TITLE: ADVANCED ANALYTICS ENGINE (TRENDS, LAGS, & DENSITY)
=============================================================================
DESCRIPTION:
This script executes "Analysis Phase 2": Deep Dive Visuals answering complex
strategic questions about Economic Lag, Seasonality, and Desert Density.

VISUALIZATIONS GENERATED:
1. THE RECESSION LAG (Early Warning System)
   - Do economic crashes predict hunger? If so, by how many months?
   - Input: Statewide Unemployment Data vs CalFresh Participation.
   - Output: Dual Axis Line Chart showing the delay between "Stress" and "Demand".

2. THE HEAT CALENDAR (True Seasonality)
   - A Heatmap (Month x Year) showing the exact intensity of demand.
   - proves if the "October Spike" is consistent or random.

3. THE SWAMP DENSITY (Geographic Saturation)
   - A Density Plot showing the distribution of "Healthy Scores" across the county.
   - Validates if the problem is "No Stores" (Desert) or "Bad Stores" (Swamp).

INPUTS:
- ../../Statewide/csv/Master data PUBLIC ACCESSIBLE (1).xlsx - Monthly.csv
- ../../Contra_Costa/csv/snap-4fymonthly-12.xlsx - Sheet1.csv
- ../../Contra_Costa/csv/modified-retail-food-environment-index-data.xlsx - modified-retail-food-environment-index-data.xlsx.csv
=============================================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- CONFIGURATION (PATHS) ---
# We assume this script is run from 'FoodBanksAnalysis/Advanced_Visuals/py'
STATEWIDE_PATH = "../../Statewide/csv/Master data PUBLIC ACCESSIBLE (1).xlsx - Monthly.csv"
CONTRA_COSTA_MONTHLY_PATH = "../../Contra_Costa/csv/snap-4fymonthly-12.xlsx - Sheet1.csv"
RFEI_PATH = "../../Contra_Costa/csv/modified-retail-food-environment-index-data.xlsx - modified-retail-food-environment-index-data.xlsx.csv"
OUTPUT_DIR = "../png/"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def analyze_recession_lag():
    """
    VISUAL A: THE RECESSION LAG (SPLIT VIEW)
    Splits Unemployment and Hunger into two stacked charts to avoid overlapping.
    Uses vertical lines to visually connect the 'Stress Peak' to the 'Hunger Peak'.
    """
    print("\n--- GENERATING: Recession Lag Chart (Split View) ---")
    if not os.path.exists(STATEWIDE_PATH):
        print(f"Error: File not found {STATEWIDE_PATH}")
        return

    try:
        # Fix: Use header=1 as per original script logic
        df = pd.read_csv(STATEWIDE_PATH, header=1)
        
        # 1. Clean Date
        df['Date'] = pd.to_datetime(df['Date'], format='%b-%y', errors='coerce')
        df = df.dropna(subset=['Date']).sort_values('Date')

        # 2. Clean Metric Columns
        for col in ['CalFresh Persons', 'Unemployment Monthly']:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace(',', '').str.replace('%', '').str.replace('%', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 3. Smoothing (Rolling Average)
        df['Unemployment_Smooth'] = df['Unemployment Monthly'].rolling(window=3).mean()
        df['Hunger_Smooth'] = df['CalFresh Persons'].rolling(window=3).mean()
        
        # 4. Find the Peaks
        covid_era = df[(df['Date'].dt.year >= 2020) & (df['Date'].dt.year <= 2021)]
        unemp_peak_date = covid_era.loc[covid_era['Unemployment_Smooth'].idxmax()]['Date']
        hunger_peak_date = covid_era.loc[covid_era['Hunger_Smooth'].idxmax()]['Date']
        
        lag_days = (hunger_peak_date - unemp_peak_date).days
        lag_months = round(lag_days / 30)

        # 5. Plot (Split Subplots)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

        # Top Plot: Unemployment
        color_stress = '#d62728' # Red
        ax1.plot(df['Date'], df['Unemployment_Smooth'], color=color_stress, linewidth=2)
        ax1.set_ylabel('Unemployment %', color=color_stress, fontweight='bold')
        ax1.set_title('1. ECONOMIC STRESS PEAKS FIRST (Unemployment)', loc='left', fontsize=12, fontweight='bold', color=color_stress)
        ax1.grid(True, alpha=0.3)
        ax1.fill_between(df['Date'], df['Unemployment_Smooth'], color=color_stress, alpha=0.1) # Soft fill

        # Low Plot: Hunger
        color_hunger = '#1f77b4' # Blue
        ax2.plot(df['Date'], df['Hunger_Smooth'], color=color_hunger, linewidth=3)
        ax2.set_ylabel('Food Bank Demand', color=color_hunger, fontweight='bold')
        ax2.set_title(f'2. HUNGER PEAKS {lag_months} MONTHS LATER (Demand)', loc='left', fontsize=12, fontweight='bold', color=color_hunger)
        ax2.grid(True, alpha=0.3)
        ax2.fill_between(df['Date'], df['Hunger_Smooth'], color=color_hunger, alpha=0.1) # Soft fill
        
        # 6. Draw "The Connection" (Vertical Lines spanning both charts)
        # We draw on the 'fig' coordinates or use shading
        
        # Mark Peak 1 (Red) on Top Chart
        ax1.axvline(unemp_peak_date, color=color_stress, linestyle='--', alpha=0.8, ymax=1)
        ax1.text(unemp_peak_date, df['Unemployment_Smooth'].max(), ' STRESS PEAK', color=color_stress, fontweight='bold', ha='left')

        # Mark Peak 1 (Red) on BOTTOM Chart too (Ghost line)
        ax2.axvline(unemp_peak_date, color=color_stress, linestyle=':', alpha=0.5)

        # Mark Peak 2 (Blue) on Bottom Chart
        ax2.axvline(hunger_peak_date, color=color_hunger, linestyle='--', alpha=0.8)
        ax2.text(hunger_peak_date, df['Hunger_Smooth'].max(), ' DEMAND PEAK', color=color_hunger, fontweight='bold', ha='left')
        
        # Highlight gap region on Bottom Chart
        ax2.axvspan(unemp_peak_date, hunger_peak_date, color='gray', alpha=0.1, label='The Lag Period')

        plt.xlabel('Date')
        fig.suptitle(f"THE RECESSION LAG: Hunger follows Stress by {lag_months} Months", fontweight='bold', fontsize=16)
        plt.tight_layout()
        
        save_path = os.path.join(OUTPUT_DIR, "recession_lag.png")
        plt.savefig(save_path)
        print(f"Saved: {save_path}")

    except Exception as e:
        print(f"Failed to generate Recession Lag: {e}")


def analyze_heat_calendar():
    """
    VISUAL B: THE HEAT CALENDAR
    Heatmap of Month vs Year to show demand intensity.
    """
    print("\n--- GENERATING: Heat Calendar ---")
    if not os.path.exists(CONTRA_COSTA_MONTHLY_PATH):
        print(f"Error: File not found {CONTRA_COSTA_MONTHLY_PATH}")
        return

    try:
        # Load Data (finding header row logic copied from contra_costa_analysis.py)
        with open(CONTRA_COSTA_MONTHLY_PATH, 'r') as f:
            lines = f.readlines()
        header_row = -1
        for i, line in enumerate(lines[:20]):
            if "Participation Persons" in line:
                header_row = i
                break
        
        df = pd.read_csv(CONTRA_COSTA_MONTHLY_PATH, header=header_row)
        
        # Dynamic Column Finding
        cols = df.columns.tolist()
        date_col = cols[0]
        part_persons_col = next((c for c in cols if "Participation Persons" in c), None)

        # Clean Date
        df = df[~df[date_col].astype(str).str.startswith('FY', na=False)]
        df = df[~df[date_col].astype(str).str.contains('ANNUAL', na=False)]
        df['parsed_date'] = pd.to_datetime(df[date_col], format='%b %Y', errors='coerce')
        df = df.dropna(subset=['parsed_date'])
        
        # Clean Numbers
        if df[part_persons_col].dtype == object:
            df[part_persons_col] = df[part_persons_col].astype(str).str.replace(',', '').str.replace('%', '').str.strip()
        df[part_persons_col] = pd.to_numeric(df[part_persons_col], errors='coerce')

        # Extract Month/Year
        df['Year'] = df['parsed_date'].dt.year
        df['Month'] = df['parsed_date'].dt.strftime('%b')
        
        # Order months correctly for the heatmap
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        df['Month'] = pd.Categorical(df['Month'], categories=month_order, ordered=True)

        # Pivot to Matrix: Rows=Year, Cols=Month, Values=Participants
        heatmap_data = df.pivot(index='Year', columns='Month', values=part_persons_col)
        
        # Plot
        plt.figure(figsize=(12, 5))
        sns.heatmap(heatmap_data, annot=True, fmt=".0f", cmap="YlOrRd", linewidths=.5)
        plt.title('The Heat Calendar: When Does Demand Actually Spike?', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        save_path = os.path.join(OUTPUT_DIR, "seasonal_heatmap.png")
        plt.savefig(save_path)
        print(f"Saved: {save_path}")

    except Exception as e:
        print(f"Failed to generate Heat Calendar: {e}")


def analyze_swamp_density():
    """
    VISUAL C: THE FOOD SWAMP CLUSTER (SIMPLIFIED)
    Replaces the confusing KDE plot with a clean Scatter Plot.
    Identifies 'Swamps' clearly as High Density (Lots of Stores) but Low Quality (Few Healthy).
    """
    print("\n--- GENERATING: Food Swamp Cluster ---")
    if not os.path.exists(RFEI_PATH):
        print(f"Error: File not found {RFEI_PATH}")
        return

    try:
        df = pd.read_csv(RFEI_PATH)
        cc_df = df[(df['county_name'] == 'Contra Costa') & (df['geotype'] == 'CT')].copy()

        # Calculate Healthy Ratio for Color Scaling
        # Avoid division by zero
        cc_df['Healthy_Ratio'] = cc_df.apply(lambda row: row['numerator'] / row['denominator'] if row['denominator'] > 0 else 0, axis=1)
        
        # Force geoname to numeric for pointers
        cc_df['geoname'] = pd.to_numeric(cc_df['geoname'], errors='coerce')

        plt.figure(figsize=(10, 7))
        
        # 1. Plot the Scatter
        # X = Total Stores (Infrastructure)
        # Y = Healthy Stores (Access)
        # Color = The "Healhiness Score" (Darker Green = Better)
        sc = plt.scatter(
            cc_df['denominator'], 
            cc_df['numerator'], 
            c=cc_df['Healthy_Ratio'], 
            cmap='RdYlGn', 
            s=100, 
            edgecolors='k', 
            alpha=0.7
        )
        
        plt.colorbar(sc, label='Healthy Store Ratio (0% = Red, 100% = Green)')
        
        # 2. Define and Draw the "Swamp Zone"
        plt.axvspan(10, cc_df['denominator'].max(), ymin=0, ymax=0.2, color='orange', alpha=0.1)
        
        # 3. Define "Deserts" (0 Stores)
        plt.plot(0, 0, marker='X', color='red', markersize=20, label='Food Deserts (0 Stores)')

        # --- ANNOTATIONS WITH FOOTER LAYOUT ---
        
        # "The Footer Strategy": Use figure coordinates to place text at the absolute bottom
        # preventing it from ever touching the X-axis label.
        
        # A. Deserts Label (Bottom Left Footer)
        plt.annotate(
            'DESERTS\n(No Access)', 
            xy=(0, 0),         # Point to Grid (0,0)
            xycoords='data',
            xytext=(0.2, 0.05), # Point to Bottom-Left of Image (Absolute)
            textcoords='figure fraction',
            arrowprops=dict(facecolor='red', shrink=0.05),
            color='red', 
            fontweight='bold',
            fontsize=11,
            bbox=dict(facecolor='white', alpha=0.9, edgecolor='red', boxstyle='round,pad=0.5'),
            ha='center'
        )

        # B. Swamps Label (Bottom Right Footer)
        plt.annotate(
            'THE SWAMP ZONE\n(Clustered Options, No Health)', 
            xy=(15, 0),          # Point to Swamp Zone
            xycoords='data',
            xytext=(0.7, 0.05),  # Point to Bottom-Right of Image (Absolute)
            textcoords='figure fraction',
            arrowprops=dict(facecolor='darkorange', shrink=0.05),
            color='darkorange', 
            fontweight='bold', 
            fontsize=11,
            bbox=dict(facecolor='white', alpha=0.9, edgecolor='darkorange', boxstyle='round,pad=0.5'),
            ha='center'
        )

        # C. Highlight Specific Examples
        try:
            # Oasis (Kensington)
            oasis = cc_df[cc_df['geoname'] == 3100].iloc[0]
            plt.annotate(
                'Kensington\n(Healthy Oasis)', 
                xy=(oasis['denominator'], oasis['numerator']), 
                xytext=(oasis['denominator'], oasis['numerator'] + 3),
                arrowprops=dict(facecolor='green', shrink=0.05),
                color='darkgreen', fontweight='bold', ha='center',
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='green')
            )
            
            # Swamp (Antioch)
            swamp = cc_df[cc_df['geoname'] == 3390.02].iloc[0]
            plt.annotate(
                'Antioch\n(Food Swamp)', 
                xy=(swamp['denominator'], swamp['numerator']), 
                xytext=(swamp['denominator'], swamp['numerator'] + 3), 
                arrowprops=dict(facecolor='red', shrink=0.05),
                color='darkred', fontweight='bold', ha='center',
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='red')
            )
        except Exception as ex:
            print(f"Could not annotate examples: {ex}")

        # C. The Dot Definition (Top Left - Safe Zone)
        # Moved to Top-Left to avoid covering the "Green Oasis" at (11, 6)
        plt.annotate(
            'Each Dot = 1 Neighborhood', 
            xy=(2, 0.5), 
            xytext=(3, 12), 
            arrowprops=dict(facecolor='black', arrowstyle='->', connectionstyle="arc3,rad=.2"),
            color='black', 
            fontweight='bold',
            fontsize=10,
            bbox=dict(facecolor='white', alpha=1.0, edgecolor='black'),
            ha='left'
        )

        # Formatting
        plt.title('The Food Landscape: Pinpointing the "Swamps"', fontsize=14, fontweight='bold')
        
        # MASSIVE BOTTOM MARGIN to create the "Footer Space"
        plt.subplots_adjust(bottom=0.35)
        
        plt.xlabel('Total Food Retailers (Volume of Options)', fontsize=12)
        plt.ylabel('Number of Healthy Food Retailers', fontsize=12)
        plt.grid(True, alpha=0.3)
        # plt.legend() Removed as requested
        
        save_path = os.path.join(OUTPUT_DIR, "food_swamp_density.png")
        # bbox_inches='tight' helps ensure the footer text isn't cropped, 
        # but sometimes conflicts with absolute positioning. 
        # Since we used subplots_adjust, the figure size is respected.
        plt.savefig(save_path) 
        print(f"Saved: {save_path}")
        
    except Exception as e:
        print(f"Failed to generate Swamp Density: {e}")


if __name__ == "__main__":
    print("Starting Advanced Analysis...")
    analyze_recession_lag()
    analyze_heat_calendar()
    analyze_swamp_density()
    print("Done.")
