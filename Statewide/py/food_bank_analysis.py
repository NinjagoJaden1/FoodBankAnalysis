
import pandas as pd  # Import pandas for data manipulation (DataFrames)
import numpy as np   # Import numpy for numerical operations
import matplotlib.pyplot as plt  # Import matplotlib for creating plots
import seaborn as sns  # Import seaborn for nicer looking plots
import glob  # Import glob to find files matching a pattern
import os    # Import os to interact with the operating system (check files)
import sys   # Import sys to access system-specific parameters (like exit)

# Configure plotting style to make charts look professional
plt.style.use('ggplot')       # Use the 'ggplot' style (gray background, grid)
sns.set_palette("tab10")      # Set the color palette to 'tab10' (10 distinct colors)

def load_and_clean_data(filepath):
    """
    Loads the food bank dataset from a CSV or Excel file, fixes date formats, 
    and cleans up text in numeric columns so they can be analyzed.
    """
    # Check if the file actually exists at the given path
    if not os.path.exists(filepath):
        print(f"ERROR: File not found at {filepath}")
        return None

    try:
        # Load the data. We use header=1 because the first row (index 0) is a description, not headers.
        if filepath.lower().endswith('.csv'):
            # Read CSV file. low_memory=False prevents warnings about mixed types in large files
            df = pd.read_csv(filepath, header=1, low_memory=False)
        else:
            # Read Excel file if the extension matches .xls or .xlsx
            df = pd.read_excel(filepath, header=1)
        
        # Define the list of columns we actually need for this analysis
        target_cols = [
            'Date', 
            'County', 
            'CalFresh Households', 
            'CalFresh Persons', 
            'Unemployment Monthly'
        ]
        
        # Check if any of these required columns are missing from the file
        missing_cols = [c for c in target_cols if c not in df.columns]
        if missing_cols:
            # If missing, print an error and the first 10 columns found (for debugging)
            print(f"ERROR: Missing expected columns: {missing_cols}")
            print("Available columns snippet:", list(df.columns[:10]))
            return None
            
        # Create a new DataFrame with only the columns we need (copy prevents warnings)
        df_subset = df[target_cols].copy()
        
        # DEBUG: Print sample dates and counties to help diagnose parsing issues
        print("\nDEBUG - Sample 'Date' values:")
        print(df_subset['Date'].dropna().unique()[:10])
        print("\nDEBUG - Sample 'County' values:")
        print(df_subset['County'].dropna().unique()[:10])

        # 1. Parse Date - The specific format identified is 'Jan-14' (Month-Year)
        # We tell pandas to expect '%b-%y' (e.g., 'Jan-14'). errors='coerce' turns bad dates into NaT (Not a Time)
        df_subset['Date'] = pd.to_datetime(df_subset['Date'], format='%b-%y', errors='coerce')
        
        # 2. Clean numeric columns (they might contain commas, stars, or percenages as text)
        numeric_cols = ['CalFresh Households', 'CalFresh Persons', 'Unemployment Monthly']
        
        print("\nDEBUG - Sample numeric column values (before conversion):")
        for col in numeric_cols:
            # Print sample values to see what we are dealing with (e.g., "1,200", "5.4%")
            print(f" -- {col}: {df_subset[col].dropna().unique()[:10]}")
            
        for col in numeric_cols:
            # If the column is stored as text (object), remove artifacts
            if df_subset[col].dtype == object:
                # Remove commas (','), asterisks ('*'), and percent signs ('%')
                df_subset[col] = df_subset[col].astype(str).str.replace(',', '').str.replace('*', '').str.replace('%', '').str.strip()
            
            # Convert the cleaned text to specific numbers (floats/ints). 
            # errors='coerce' turns anything that fails (like 'N/A') into NaN (Not a Number)
            df_subset[col] = pd.to_numeric(df_subset[col], errors='coerce')
            
        # 3. Filter valid rows
        # Drop rows where 'Date' didn't parse correctly
        df_clean = df_subset.dropna(subset=['Date'])
        
        # Print a summary of how much data we kept vs lost
        print("\nData Cleaning Summary:")
        print(f"Original Row Count: {len(df)}")
        print(f"Cleaned Row Count: {len(df_clean)}")
        print("\nMissing Values by Column:")
        print(df_clean.isnull().sum())
        
        # Return the cleaned DataFrame
        return df_clean
    
    except Exception as e:
        # If anything crashes in the try block, catch the error and print it
        print(f"Error loading/cleaning data: {e}")
        return None

def plot_statewide_trend(df):
    """
    Filters for statewide data and plots the trend of participation over time.
    """
    # Try to find rows where County explicitly says 'Statewide'
    statewide = df[df['County'] == 'Statewide'].copy()
    
    # If no such rows exist (data issue), manually sum up all counties instead
    if statewide.empty:
        print("Warning: No 'Statewide' rows found. Aggregating all counties...")
        # Sum numeric columns group by Date. This recreates the statewide total.
        statewide = df[df['County'] != 'Statewide'].groupby('Date').sum().reset_index()
    
    # Sort by date so lines connect in the right order
    statewide = statewide.sort_values('Date')
    
    # Create the plot figure
    plt.figure(figsize=(12, 6))
    # Plot Households (Solid line)
    plt.plot(statewide['Date'], statewide['CalFresh Households'], label='CalFresh Households', linewidth=2)
    # Plot Persons (Dashed line)
    plt.plot(statewide['Date'], statewide['CalFresh Persons'], label='CalFresh Persons', linestyle='--', alpha=0.7)
    
    # Add labels and title
    plt.title("Statewide CalFresh Participation Trend")
    plt.ylabel("Count")
    plt.xlabel("Date")
    plt.legend()  # Show the legend identifying lines
    plt.grid(True) # Add grid lines for readability
    plt.tight_layout() # Fix layout spacing
    plt.tight_layout() 
    plt.savefig("statewide_trend.png") # Save to file
    print("\nSaved plot to: statewide_trend.png")
    
    return statewide

def analyze_spikes(df):
    """
    Detects sudden spikes in demand.
    Criteria: 
    1. MoM Percent Change (how much did it grow vs last month?)
    2. Z-score (is this growth statistically unusual? > 2 sigmas)
    """
    df = df.copy() # Work on a copy
    # Calculate % change from previous month
    df['MoM_Change'] = df['CalFresh Households'].pct_change()
    
    # Calculate Z-score: (Value - Mean) / Standard Deviation
    # This measures how many "standard deviations" away from normal the change is.
    df['MoM_Zscore'] = (df['MoM_Change'] - df['MoM_Change'].mean()) / df['MoM_Change'].std()
    
    # Define a "spike" as an event where the Z-score is greater than 2 (top ~2.5% of positive shocks)
    spikes = df[df['MoM_Zscore'] > 2]
    
    print("\n=== Demand Spikes Detected (Statewide) ===")
    if not spikes.empty:
        # Print the spike dates and values
        print(spikes[['Date', 'CalFresh Households', 'MoM_Change', 'MoM_Zscore']].to_string(index=False))
    else:
        print("No significant positive spikes (Z-score > 2) detected.")
        
    # Plot the Month-over-Month changes and highlight spikes in red
    plt.figure(figsize=(12, 6))
    plt.plot(df['Date'], df['MoM_Change'], label='MoM % Change', color='grey', alpha=0.5)
    plt.scatter(spikes['Date'], spikes['MoM_Change'], color='red', label='Spike (> 2 std dev)', s=100, zorder=5)
    
    # Add Threshold lines
    plt.title("Statewide Demand Spikes (Month-over-Month Change)")
    plt.axhline(0, color='black', linewidth=0.5) # Zero line
    # Plot the standard deviation threshold line
    plt.axhline(df['MoM_Change'].mean() + 2*df['MoM_Change'].std(), color='red', linestyle='--', label='Threshold')
    plt.legend()
    plt.ylabel("MoM % Change")
    plt.savefig("demand_spikes.png")
    print("Saved plot to: demand_spikes.png")

def analyze_seasonality(df):
    """
    Decomposes the time series into Trend, Seasonal, and Residual (Noise) components.
    """
    from statsmodels.tsa.seasonal import seasonal_decompose # Import library for decomposition
    
    # Set the 'Date' as the index and force frequency to 'MS' (Month Start)
    df_ts = df.set_index('Date').asfreq('MS')
    
    # Values can't be missing for decomposition, so interpolate (fill gaps linearly)
    df_ts['CalFresh Households'] = df_ts['CalFresh Households'].interpolate()
    
    # Check if we have enough data (at least 2 years needed to find a yearly pattern)
    if len(df_ts) < 24:
        print("\nWarning: Not enough data for seasonal decomposition (need > 2 years).")
        return

    try:
        # Perform decomposition (Additive model: Observed = Trend + Seasonal + Residual)
        decomp = seasonal_decompose(df_ts['CalFresh Households'], model='additive', period=12)
        
        # Create a figure with 4 subplots sharing the x-axis
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
        decomp.observed.plot(ax=ax1, title='Observed (Raw Data)')
        decomp.trend.plot(ax=ax2, title='Trend (Long-term direction)')
        decomp.seasonal.plot(ax=ax3, title='Seasonal (Repeating Pattern)')
        decomp.resid.plot(ax=ax4, title='Residual (Noise/Unexplained)')
        plt.tight_layout()
        plt.savefig("seasonality_decomposition.png")
        print("Saved plot to: seasonality_decomposition.png")
        
        # Identify which month usually has the highest demand (Seasonal Peak)
        # Group by month (1=Jan, 12=Dec) and take the mean of the seasonal component
        seasonal = decomp.seasonal.groupby(decomp.seasonal.index.month).mean()
        peak_month = seasonal.idxmax() # Index of the max value
        print(f"\nSeasonal Peak Month: {peak_month}")
        print("Seasonal Index by Month:")
        print(seasonal)
        
    except Exception as e:
        print(f"Error in seasonality analysis: {e}")

def investigate_anomaly(df, date_str):
    """
    Zooms in on data around a specific date to inspect an anomaly.
    """
    target_date = pd.to_datetime(date_str) # Convert string to date object
    start_date = target_date - pd.DateOffset(months=3) # 3 months before
    end_date = target_date + pd.DateOffset(months=3)   # 3 months after
    
    # Filter the window
    window = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    print(f"\n=== Anomaly Investigation ({date_str}) ===")
    # Print the window data
    print(window[['Date', 'CalFresh Households', 'MoM_Change']].to_string(index=False))

def analyze_correlation(df):
    """
    Analyzes if Unemployment predicts CalFresh demand.
    """
    # 1. Scatter plot: Visual check for relationship
    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=df, x='Unemployment Monthly', y='CalFresh Households')
    plt.title("CalFresh Demand vs Unemployment Rate")
    plt.xlabel("Unemployment Rate")
    plt.ylabel("CalFresh Households")
    plt.savefig("unemployment_correlation.png")
    print("\nSaved plot to: unemployment_correlation.png")
    
    # 2. Correlation Matrix: Statistical check (Pearson correlation)
    corr = df[['CalFresh Households', 'Unemployment Monthly']].corr()
    print("\nCorrelation Matrix:")
    print(corr)
    
    # 3. Lag Analysis: Does unemployment TODAY predict demand in the FUTURE?
    df = df.copy()
    for lag in range(1, 7): # Check 1 to 6 months lag
        # Shift unemployment forward by 'lag' months
        df[f'Unemployment_Lag_{lag}'] = df['Unemployment Monthly'].shift(lag)
        
    # Calculate correlation between Demand and Lagged Unemployment
    lag_corr = df[['CalFresh Households'] + [f'Unemployment_Lag_{i}' for i in range(1, 7)]].corr()['CalFresh Households']
    print("\nLagged Correlation (Unemployment predicting Demand):")
    # Drop the self-correlation (1.0) and print the rest
    print(lag_corr.drop('CalFresh Households'))

def main():
    # Define potential filenames
    filenames = [
        "../csv/Master data PUBLIC ACCESSIBLE (1).xlsx - Monthly.csv",
        "../csv/Master data PUBLIC ACCESSIBLE (1).xlsx",
        "../csv/data.csv"
    ]
    
    # Loop through filenames to find one that exists
    filepath = None
    for fname in filenames:
        if os.path.exists(fname):
            filepath = fname
            break
            
    # If no file found, exit the program
    if filepath is None:
        print("DATASET NOT FOUND.")
        sys.exit(1)
        
    print(f"Loading dataset from: {filepath}")
    # Run the loading and cleaning function
    df = load_and_clean_data(filepath)
    
    # If data loaded successfully, proceed with analysis
    if df is not None:
        print("\nData Loaded & Cleaned Successfully.")
        # Plot trend and get the statewide dataframe
        statewide_df = plot_statewide_trend(df)
        
        # Calculate MoM Change globally so other functions can use it
        statewide_df['MoM_Change'] = statewide_df['CalFresh Households'].pct_change()
        
        # Run various analysis modules
        analyze_spikes(statewide_df)
        investigate_anomaly(statewide_df, '2019-03-01') # Look at the specific March 2019 event
        analyze_seasonality(statewide_df)
        analyze_correlation(statewide_df)

if __name__ == "__main__":
    main()
