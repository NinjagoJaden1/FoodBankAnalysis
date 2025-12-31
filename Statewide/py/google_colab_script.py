
# ==========================================
# INSTRUCTIONS FOR GOOGLE COLAB
# ==========================================
# 1. Copy this entire code block into a cell in Google Colab.
# 2. Upload your dataset (csv or xlsx) to the Colab files area (folder icon on the left).
#    OR simply run this script, and it will ask you to upload the file if it can't find it.
# 3. Requires 'statsmodels'. If not installed, uncomment and run the following line in a separate cell:
#    !pip install statsmodels
# ==========================================

import pandas as pd  # Import pandas for data manipulation
import numpy as np   # Import numpy for math
import matplotlib.pyplot as plt  # Import plotting library
import seaborn as sns  # Import seaborn for styling
from sklearn.metrics import mean_absolute_error, mean_squared_error # Import error metrics
from statsmodels.tsa.statespace.sarimax import SARIMAX  # Import SARIMA model
from statsmodels.tsa.holtwinters import ExponentialSmoothing # Import Holt-Winters model
import sys  # Import system library
import os   # Import OS library

# Configure plotting style
plt.style.use('ggplot')       # Use ggplot style
sns.set_palette("tab10")      # Set color palette

def load_and_clean_data(filepath):
    """
    Loads the food bank dataset from a CSV or Excel file, fixes date formats, 
    and cleans up text in numeric columns so they can be analyzed.
    """
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
        
        # Define the columns we need
        target_cols = ['Date', 'County', 'CalFresh Households', 'CalFresh Persons', 'Unemployment Monthly']
        
        # Check for missing columns
        missing_cols = [c for c in target_cols if c not in df.columns]
        if missing_cols:
            print(f"ERROR: Missing expected columns: {missing_cols}")
            return None
            
        # Create a new DataFrame with only the columns we need
        df_subset = df[target_cols].copy()
        
        print(f"Loaded {len(df_subset)} rows. Cleaning data...")

        # 1. Parse Date - The specific format identified is 'Jan-14' (Month-Year)
        df_subset['Date'] = pd.to_datetime(df_subset['Date'], format='%b-%y', errors='coerce')
        
        # 2. Clean numeric columns (remove commas, stars, percent signs)
        numeric_cols = ['CalFresh Households', 'CalFresh Persons', 'Unemployment Monthly']
        for col in numeric_cols:
            if df_subset[col].dtype == object:
                df_subset[col] = df_subset[col].astype(str).str.replace(',', '').str.replace('*', '').str.replace('%', '').str.strip()
            # Convert to numeric, errors to NaN
            df_subset[col] = pd.to_numeric(df_subset[col], errors='coerce')
            
        # 3. Filter valid rows (drop rows where Date didn't parse)
        df_clean = df_subset.dropna(subset=['Date'])
        
        # Return the cleaned DataFrame
        return df_clean
    
    except Exception as e:
        print(f"Error loading/cleaning data: {e}")
        return None

def plot_statewide_trend(df):
    """
    Filters for statewide data and plots the trend of participation over time.
    """
    # Try to find rows where County explicitly says 'Statewide'
    statewide = df[df['County'] == 'Statewide'].copy()
    
    # If no such rows exist, sum all counties
    if statewide.empty:
        print("Aggregating county data to create Statewide totals...")
        statewide = df[df['County'] != 'Statewide'].groupby('Date').sum().reset_index()
    
    # Sort by date
    statewide = statewide.sort_values('Date')
    
    # Create the plot figure
    plt.figure(figsize=(12, 6))
    plt.plot(statewide['Date'], statewide['CalFresh Households'], label='CalFresh Households', linewidth=2)
    plt.plot(statewide['Date'], statewide['CalFresh Persons'], label='CalFresh Persons', linestyle='--', alpha=0.7)
    
    plt.title("Statewide CalFresh Participation Trend")
    plt.ylabel("Count")
    plt.xlabel("Date")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show() # Display plot in Colab
    
    return statewide

def analyze_spikes(df):
    """
    Detects sudden spikes in demand (Z-score > 2).
    """
    df = df.copy()
    # Calculate % change from previous month
    df['MoM_Change'] = df['CalFresh Households'].pct_change()
    
    # Calculate Z-score (Standard deviations from mean)
    df['MoM_Zscore'] = (df['MoM_Change'] - df['MoM_Change'].mean()) / df['MoM_Change'].std()
    
    # Define a "spike" as Z-score > 2
    spikes = df[df['MoM_Zscore'] > 2]
    
    print("\n=== Demand Spikes Detected (Statewide) ===")
    if not spikes.empty:
        print(spikes[['Date', 'CalFresh Households', 'MoM_Change', 'MoM_Zscore']].to_string(index=False))
    else:
        print("No significant positive spikes (Z-score > 2) detected.")
        
    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df['Date'], df['MoM_Change'], label='MoM % Change', color='grey', alpha=0.5)
    plt.scatter(spikes['Date'], spikes['MoM_Change'], color='red', label='Spike (> 2 std dev)', s=100, zorder=5)
    plt.axhline(0, color='black', linewidth=0.5)
    plt.axhline(df['MoM_Change'].mean() + 2*df['MoM_Change'].std(), color='red', linestyle='--', label='Threshold')
    plt.title("Statewide Demand Spikes")
    plt.legend()
    plt.show()

def analyze_seasonality(df):
    """
    Decomposes the time series into Trend, Seasonal, and Residual components.
    """
    from statsmodels.tsa.seasonal import seasonal_decompose
    
    # Set Date as index, frequency Month Start
    df_ts = df.set_index('Date').asfreq('MS')
    df_ts['CalFresh Households'] = df_ts['CalFresh Households'].interpolate() # Fill gaps
    
    if len(df_ts) < 24:
        print("\nWarning: Not enough data for seasonal decomposition.")
        return

    try:
        decomp = seasonal_decompose(df_ts['CalFresh Households'], model='additive', period=12)
        
        # Plot decomposition (4 subplots)
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
        decomp.observed.plot(ax=ax1, title='Observed')
        decomp.trend.plot(ax=ax2, title='Trend')
        decomp.seasonal.plot(ax=ax3, title='Seasonal')
        decomp.resid.plot(ax=ax4, title='Residual')
        plt.tight_layout()
        plt.show()
        
        # Identify Seasonal Peak
        seasonal = decomp.seasonal.groupby(decomp.seasonal.index.month).mean()
        peak_month = seasonal.idxmax()
        print(f"\nSeasonal Peak Month: {peak_month}")
        
    except Exception as e:
        print(f"Error in seasonality analysis: {e}")

def investigate_anomaly(df, date_str):
    """
    Inspects data around a specific date.
    """
    target_date = pd.to_datetime(date_str)
    start_date = target_date - pd.DateOffset(months=3)
    end_date = target_date + pd.DateOffset(months=3)
    
    window = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    if 'MoM_Change' in window.columns:
        print(f"\n=== Anomaly Investigation ({date_str}) ===")
        print(window[['Date', 'CalFresh Households', 'MoM_Change']].to_string(index=False))

def analyze_correlation(df):
    """
    Analyzes if Unemployment predicts CalFresh demand.
    """
    # Scatter plot
    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=df, x='Unemployment Monthly', y='CalFresh Households')
    plt.title("CalFresh Demand vs Unemployment Rate")
    plt.show()
    
    # Correlation Matrix
    corr = df[['CalFresh Households', 'Unemployment Monthly']].corr()
    print("\nCorrelation Matrix:")
    print(corr)
    
    # Lag Analysis
    df = df.copy()
    for lag in range(1, 7):
        df[f'Unemployment_Lag_{lag}'] = df['Unemployment Monthly'].shift(lag)
        
    lag_corr = df[['CalFresh Households'] + [f'Unemployment_Lag_{i}' for i in range(1, 7)]].corr()['CalFresh Households']
    print("\nLagged Correlation (Unemployment predicting Demand):")
    print(lag_corr.drop('CalFresh Households'))

# --- PREDICTIVE FUNCTIONS ---

def train_test_split_ts(df, test_months=6):
    train = df.iloc[:-test_months]
    test = df.iloc[-test_months:]
    return train, test

def evaluate_model(y_true, y_pred, model_name):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    
    print(f"\nModel: {model_name}")
    print(f"MAE: {mae:,.0f} | MAPE: {mape:.2f}%")
    return {'Model': model_name, 'MAE': mae, 'RMSE': rmse, 'MAPE': mape}

def run_predictions(df):
    """
    Runs predictive models (Baseline, Holt-Winters, SARIMA).
    """
    results = []
    
    # Check for Structural Break in March 2019
    break_date = pd.to_datetime('2019-03-01')
    pre_break = df[df['Date'] < break_date]['CalFresh Households'].mean()
    post_break = df[df['Date'] >= break_date]['CalFresh Households'].mean()
    
    if post_break > 1.5 * pre_break:
        print("\n>> Detected major level shift (March 2019). Using only Post-2019 data for modeling.")
        model_df = df[df['Date'] >= break_date].copy()
    else:
        model_df = df.copy()
        
    model_df = model_df.set_index('Date')['CalFresh Households']
    model_df = model_df.asfreq('MS').interpolate()
    
    # Split Data (Leave out last 6 months for testing)
    train, test = train_test_split_ts(model_df, test_months=6)
    
    # 1. Naive Model (Last Value)
    y_pred_naive = [train.iloc[-1]] * len(test)
    results.append(evaluate_model(test, y_pred_naive, "Naive (Last Value)"))
    
    # 2. Seasonal Naive (Last 12 Month Value)
    y_pred_snaive = []
    for date in test.index:
        month_ago_12 = date - pd.DateOffset(months=12)
        if month_ago_12 in train.index:
             y_pred_snaive.append(train.loc[month_ago_12])
        else:
             y_pred_snaive.append(train.iloc[-1])
    results.append(evaluate_model(test, y_pred_snaive, "Seasonal Naive"))

    # 3. Holt-Winters
    try:
        model_hw = ExponentialSmoothing(train, seasonal='add', seasonal_periods=12).fit()
        y_pred_hw = model_hw.forecast(len(test))
        results.append(evaluate_model(test, y_pred_hw, "Holt-Winters"))
    except Exception as e:
        print(f"HW Model failed: {e}")

    # 4. SARIMA
    try:
        model_sarima = SARIMAX(train, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12), enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
        y_pred_sarima = model_sarima.forecast(len(test))
        results.append(evaluate_model(test, y_pred_sarima, "SARIMA"))
    except Exception as e:
         print(f"SARIMA failed: {e}")
         
    # Plot Comparison
    plt.figure(figsize=(15, 8))
    plt.plot(train.index, train, label='Train Data')
    plt.plot(test.index, test, label='Actual Test Data', linewidth=2, color='black')
    if 'y_pred_hw' in locals():
        plt.plot(test.index, y_pred_hw, label='Holt-Winters', linestyle='--')
    if 'y_pred_sarima' in locals():
        plt.plot(test.index, y_pred_sarima, label='SARIMA', linestyle='--')
    plt.title("Predictive Model Comparison")
    plt.legend()
    plt.show()

def main():
    print("=== FOOD BANK DEMAND ANALYSIS (GOOGLE COLAB VERSION) ===")
    
    # Try to find file automatically
    filenames = [
        "Master data PUBLIC ACCESSIBLE (1).xlsx - Monthly.csv",
        "Master data PUBLIC ACCESSIBLE (1).xlsx",
        "data.csv"
    ]
    
    filepath = None
    for fname in filenames:
        if os.path.exists(fname):
            filepath = fname
            break
            
    # If not found, ask user to upload (Colab specific)
    if filepath is None:
        print("\nDataset not found in current directory.")
        print("Please upload your CSV/Excel file now...")
        try:
            from google.colab import files
            uploaded = files.upload()
            if uploaded:
                filepath = list(uploaded.keys())[0]
                print(f"Uploaded: {filepath}")
        except ImportError:
            print("Not running in Google Colab? Please manually place your file in the folder.")
            sys.exit(1)
            
    if not filepath:
        print("No file selected.")
        sys.exit(1)

    print(f"\nProcessing file: {filepath}")
    df = load_and_clean_data(filepath)
    
    if df is not None:
        print("\n--- PHASE 1: EXPLORATORY ANALYSIS ---")
        statewide_df = plot_statewide_trend(df)
        
        # Calculate MoM Change for spikes
        statewide_df['MoM_Change'] = statewide_df['CalFresh Households'].pct_change()
        
        analyze_spikes(statewide_df)
        investigate_anomaly(statewide_df, '2019-03-01')
        analyze_seasonality(statewide_df)
        analyze_correlation(statewide_df)
        
        print("\n--- PHASE 2: PREDICTIVE MODELING ---")
        run_predictions(statewide_df)
        
        print("\n=== ANALYSIS COMPLETE ===")

if __name__ == "__main__":
    main()
