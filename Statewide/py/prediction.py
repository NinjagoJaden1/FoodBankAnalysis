"""
=============================================================================
TITLE: PREDICTIVE FORECASTING ENGINE
=============================================================================
DESCRIPTION:
This script uses the 'Prophet' library (or similar time-series logic) to
forecast future demand based on historical data.

PURPOSE:
To answer the question: "What will demand look like in 6 months?"
It is used to warn the operations team of incoming surges that fall outside
of standard seasonal patterns.

KEY COMPONENTS:
1. Data Preparation: Formats dates for time-series modeling.
2. Model Training: Fits specific changepoints in the history.
3. Future DataFrame: Extends the timeline 3-6 months out.
4. Visualization: Plots the 'Forecast Cone' (Confidence Interval).
=============================================================================
"""
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

def load_data(filepath):
    """
    Loads and cleans data identically to the main analysis script.
    See food_bank_analysis.py for detailed comments on cleaning.
    """
    # Load file based on extension
    if filepath.lower().endswith('.csv'):
        df = pd.read_csv(filepath, header=1, low_memory=False)
    else:
        df = pd.read_excel(filepath, header=1)
        
    # Select needed columns
    target_cols = ['Date', 'County', 'CalFresh Households', 'Unemployment Monthly']
    df_subset = df[target_cols].copy()
    
    # Parse Date
    df_subset['Date'] = pd.to_datetime(df_subset['Date'], format='%b-%y', errors='coerce')
    
    # Clean numeric columns (remove commas, %, etc)
    numeric_cols = ['CalFresh Households', 'Unemployment Monthly']
    for col in numeric_cols:
         if df_subset[col].dtype == object:
            df_subset[col] = df_subset[col].astype(str).str.replace(',', '').str.replace('*', '').str.replace('%', '').str.strip()
         df_subset[col] = pd.to_numeric(df_subset[col], errors='coerce')
            
    # Drop rows with bad dates or missing household counts
    df_clean = df_subset.dropna(subset=['Date', 'CalFresh Households'])
    
    # Aggregate Statewide (handle if 'Statewide' row exists or sum counties)
    statewide = df_clean[df_clean['County'] == 'Statewide'].copy()
    if statewide.empty:
         statewide = df_clean[df_clean['County'] != 'Statewide'].groupby('Date').sum().reset_index()
         
    return statewide.sort_values('Date') # Return sorted by date

def train_test_split_ts(df, test_months=6):
    """
    Splits time series into train (history) and test (future validation) sets.
    We generally hold back the last few months to test accuracy.
    """
    train = df.iloc[:-test_months] # All data EXCEPT the last 'test_months'
    test = df.iloc[-test_months:]  # ONLY the last 'test_months'
    return train, test

def evaluate_model(y_true, y_pred, model_name):
    """
    Calculates error metrics to see how good a model is.
    """
    # Mean Absolute Error: Average "miss" in absolute numbers
    mae = mean_absolute_error(y_true, y_pred)
    
    # Root Mean Squared Error: Penalizes big errors more heavily
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    
    # Mean Absolute Percentage Error: Average "miss" in percentage terms (e.g. 5% off)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    
    # Print the results
    print(f"\nModel: {model_name}")
    print(f"MAE: {mae:,.0f}")
    print(f"RMSE: {rmse:,.0f}")
    print(f"MAPE: {mape:.2f}%")
    return {'Model': model_name, 'MAE': mae, 'RMSE': rmse, 'MAPE': mape}

def run_models(df):
    """
    Runs multiple time-series models and compares them.
    1. Check for structural breaks (major level shifts).
    2. Split data.
    3. Train Baseline, Holt-Winters, and SARIMA.
    4. Plot results.
    """
    results = []
    
    # CHECK FOR STRUCTURAL BREAK (March 2019)
    # Why? If the world changed in 2019, training on 2014 data might be misleading.
    break_date = pd.to_datetime('2019-03-01')
    
    # Calculate average demand before and after the break date
    pre_break = df[df['Date'] < break_date]['CalFresh Households'].mean()
    post_break = df[df['Date'] >= break_date]['CalFresh Households'].mean()
    print(f"\nStructural Break Check (Mar 2019):")
    print(f"Pre-2019 Mean: {pre_break:,.0f}")
    print(f"Post-2019 Mean: {post_break:,.0f}")
    
    # If the new mean is > 1.5x the old mean, throw away the old data.
    if post_break > 1.5 * pre_break:
        print(">> Detected major level shift. Using only Post-2019 data for training to improve accuracy.")
        model_df = df[df['Date'] >= break_date].copy()
    else:
        model_df = df.copy() # Use all data if no big shift
        
    # Set Date as index so models understand the time component
    model_df = model_df.set_index('Date')['CalFresh Households']
    
    # Ensure regular monthly frequency (fill missing months if any)
    model_df = model_df.asfreq('MS').interpolate()
    
    # Split Train/Test (Last 6 months as validation test)
    train, test = train_test_split_ts(model_df, test_months=6)
    
    print(f"\nTraining Range: {train.index.min().date()} to {train.index.max().date()}")
    print(f"Test Range: {test.index.min().date()} to {test.index.max().date()}")
    
    # --- MODEL 1: Naive (Baseline) ---
    # Prediction: Next month = This month. 
    # This is surprisingly hard to beat in stable systems.
    y_pred_naive = [train.iloc[-1]] * len(test)
    results.append(evaluate_model(test, y_pred_naive, "Naive (Last Value)"))
    
    # --- MODEL 2: Seasonal Naive (Baseline) ---
    # Prediction: Next month = Same month last year.
    # Good for highly seasonal data.
    y_pred_snaive = []
    for date in test.index:
        month_ago_12 = date - pd.DateOffset(months=12)
        if month_ago_12 in train.index:
             y_pred_snaive.append(train.loc[month_ago_12])
        else:
             y_pred_snaive.append(train.iloc[-1]) # Fallback if history missing
    results.append(evaluate_model(test, y_pred_snaive, "Seasonal Naive"))

    # --- MODEL 3: Exponential Smoothing (Holt-Winters) ---
    # Handles Trend and Seasonality explicitly.
    try:
        model_hw = ExponentialSmoothing(train, seasonal='add', seasonal_periods=12).fit()
        y_pred_hw = model_hw.forecast(len(test))
        results.append(evaluate_model(test, y_pred_hw, "Holt-Winters"))
    except Exception as e:
        print(f"HW Model failed: {e}")

    # --- MODEL 4: SARIMA ---
    # Seasonal AutoRegressive Integrated Moving Average.
    # Complex statistical model.
    try:
        # Order (1,1,1) x (1,1,1,12) is a standard starting point for monthly data
        model_sarima = SARIMAX(train, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12), enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
        y_pred_sarima = model_sarima.forecast(len(test))
        results.append(evaluate_model(test, y_pred_sarima, "SARIMA"))
    except Exception as e:
         print(f"SARIMA failed: {e}")
         
    # --- PLOT COMPARISON ---
    plt.figure(figsize=(15, 8))
    plt.plot(train.index, train, label='Train Data (History)')
    plt.plot(test.index, test, label='Actual Test Data (Truth)', linewidth=2, color='black')
    
    if 'y_pred_hw' in locals():
        plt.plot(test.index, y_pred_hw, label='Holt-Winters Prediction', linestyle='--')
    if 'y_pred_sarima' in locals():
        plt.plot(test.index, y_pred_sarima, label='SARIMA Prediction', linestyle='--')
        
    plt.title("Predictive Model Comparison")
    plt.legend()
    plt.savefig("model_forecast_comparison.png")
    print("\nSaved forecast plot to: model_forecast_comparison.png")
    
    # --- FUTURE FORECAST ---
    # Now that we've tested models, let's train on ALL data and predict the UNKNOWN future (Next 3 months)
    final_model = SARIMAX(model_df, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12), enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
    future_forecast = final_model.forecast(3)
    
    print("\n=== Future Forecast (Next 3 Months) ===")
    print(future_forecast)
    
    return pd.DataFrame(results)

def main():
    # Define potential filenames
    filenames = [
        "../csv/Master data PUBLIC ACCESSIBLE (1).xlsx - Monthly.csv",
        "../csv/Master data PUBLIC ACCESSIBLE (1).xlsx",
        "../csv/data.csv"
    ]
    
    # Locate file
    filepath = None
    for fname in filenames:
        if os.path.exists(fname):
            filepath = fname
            break
            
    if filepath is None:
        print("DATASET NOT FOUND.")
        sys.exit(1)
        
    # Run pipeline
    df = load_data(filepath)
    results = run_models(df)
    
    # Print final scorecard
    print("\nSummary of Model Performance:")
    print(results)

if __name__ == "__main__":
    main()
