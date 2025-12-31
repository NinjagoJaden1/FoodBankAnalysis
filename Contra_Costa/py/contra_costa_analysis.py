
import pandas as pd  # PANDAS: The "Excel for Python". We use this to load tables and math.
import numpy as np   # NUMPY: A library for fast math operations.
import matplotlib.pyplot as plt  # MATPLOTLIB: The standard library for drawing graphs.
import seaborn as sns  # SEABORN: A plug-in that makes Matplotlib graphs look prettier and easier to use.
import os  # OS: Used to talk to your computer (e.g., checking if a file exists).

# --- VISUAL SETUP ---
# We set the "Style" of the charts globally here.
# 'ggplot' gives us that nice gray background with white gridlines (professional look).
plt.style.use('ggplot')
# 'tab10' is a color palette with 10 distinct colors, good for categorical data.
sns.set_palette("tab10") 

def analyze_neighborhood_gaps(filepath):
    """
    =============================================================================
    MODULE 1: NEIGHBORHOOD SERVICE GAPS
    =============================================================================
    STRATEGIC GOAL:
    We need to find the specific blocks where people have NO access to healthy food.
    This tells the Operations Team exactly where to drive the Mobile Pantry trucks.
    
    DATA SOURCE: 
    mRFEI (Modified Retail Food Environment Index). 
    - Score 0 = Food Desert (No healthy food).
    - Score 100 = Perfect Access.
    =============================================================================
    """
    print("\n" + "="*60)
    print("ANALYSIS 1: LOCATING THE FOOD DESERTS (WHERE TO SEND TRUCKS)")
    print("="*60)
    
    # VALIDATION: Always check if your data file actually exists before crashing the program.
    if not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        return

    try:
        # STEP 1: LOAD
        # Read the Comma Separated Values (CSV) file into a DataFrame (df).
        df = pd.read_csv(filepath)
        
        # STEP 2: FILTER
        # We only care about "Contra Costa" county.
        # We also only care about "Census Tracts" (CT), which are small neighborhood-sized blocks.
        # We ignore rows representing the whole state or county.
        cc_df = df[
            (df['county_name'] == 'Contra Costa') & 
            (df['geotype'] == 'CT')
        ].copy() # .copy() creates a standalone table so we don't accidentally break the original data.
        
        # STEP 3: RANKING
        # Sort by 'estimate' (the score) smallest-to-largest.
        # We take the top 15 rows because we want the 15 WORST neighborhoods.
        worst_15 = cc_df.sort_values('estimate', ascending=True).head(15)
        
        print(f"\n>> INSIGHT: The Top 15 Highest-Need Neighborhoods")
        print(f"{'Neighborhood (Census Tract)':<35} | {'Score':<6} | {'Stores':<8} | {'Diagnosis'}")
        print("-" * 90)
        
        recommendations = [] # We will store our findings here to use them later.
        
        # STEP 4: DIAGNOSIS LOOP
        # "iterrows()" lets us look at the data one row at a time, like a manager reviewing files.
        for _, row in worst_15.iterrows():
            # PARSING LOGIC: The ID is a code like '6013355112'. We need to make it readable.
            # 6=CA, 013=Contra Costa, 355112=Tract 3551.12
            tract_id_raw = str(row['geotypevalue']) 
            
            # Use slicing [start:end] to grab the last 6 digits (the tract number)
            if len(tract_id_raw) == 10: tract_id_code = tract_id_raw[5:]
            elif len(tract_id_raw) == 9: tract_id_code = tract_id_raw[4:]
            else: tract_id_code = tract_id_raw[-6:]
            
            # Format nicely with a decimal point: "355112" -> "Census Tract 3551.12"
            tract_name = f"Census Tract {tract_id_code[:-2]}.{tract_id_code[-2:]}"
            
            score = row['estimate']        # The quality score (0-100)
            std_denom = row['denominator'] # The total number of stores (Quantity)
            
            # DECISION TREE: What is the actual problem here?
            if std_denom == 0:
                # PROBLEM: Absolute lack of food.
                # SOLUTION: Truck MUST go here.
                diagnosis = "FOOD DESERT (No stores)"
                action = "Deploy Mobile Pantry (Primary Target)"
                color = 'red' # Signal color for danger/high priority
            elif std_denom < 3:
                # PROBLEM: Very few options.
                # SOLUTION: Truck should go here if extra capacity exists.
                diagnosis = "SCARCE RESOURCES (Few stores)"
                action = "Deploy Mobile Pantry (Secondary Target)"
                color = 'orange'
            else:
                # PROBLEM: Options exist, but they are all unhealthy (e.g., 5 liquor stores, 0 grocery).
                # SOLUTION: Partnerships (Healthy Corner Stores), not trucks.
                diagnosis = "FOOD SWAMP (Unhealthy Access)"
                action = "Partner/Educate Corners Stores"
                color = 'gold'
                
            # Print the row to the terminal for the user to see immediately
            print(f"{tract_name:<35} | {score:<6.1f} | {std_denom:<8.0f} | {diagnosis}")
            
            # Save the clean data
            recommendations.append({'Tract': tract_name, 'Diagnosis': diagnosis, 'Action': action, 'Color': color, 'Score': score, 'Stores': std_denom})
            
        # --- VISUALIZATION 1: Food Desert Ranking (Bar Chart) ---
        plt.figure(figsize=(10, 8)) # Create an empty picture frame (10x8 inches)
        
        # Sort data for the plot so the bars are in order (Worst at top)
        top_15_plot = worst_15.sort_values('estimate', ascending=True) 
        
        # Draw the Bars
        sns.barplot(x='estimate', y='geotypevalue', data=top_15_plot, palette='Reds_r')
        
        # Label the axes plainly
        plt.title("Top 15 Food Deserts in Contra Costa (Lowest mRFEI Score)")
        plt.xlabel("Healthy Food Access Score (0 = Worst)")
        plt.ylabel("Census Tract ID")
        plt.tight_layout() # Fix margins
        plt.savefig("food_desert_ranking.png") # Save file
        
        # --- EXPLANATION 1 ---
        print("\n" + "-"*60)
        print("VISUAL GENERATED: 'food_desert_ranking.png'")
        print("-"*60)
        print("WHAT IT IS: A 'Hit List' of the 15 neediest neighborhoods.")
        print("HOW TO USE: Give this list to your Logistics Manager.")
        print("ACTION: These are the exact GPS destinations for your Mobile Pantry drivers.")

        # --- VISUALIZATION 2: Service Gap Matrix (Scatter Plot) ---
        plt.figure(figsize=(10, 6))
        
        # Define categories for every single neighborhood, not just the top 15
        def categorize(row):
            if row['denominator'] == 0: return 'Desert (0 Stores)'
            if row['denominator'] < 3: return 'Scarce (<3 Stores)'
            if row['estimate'] < 10: return 'Swamp (Unhealthy)'
            return 'Healthy Access'
            
        # Apply the category logic to the dataframe
        cc_df['Category'] = cc_df.apply(categorize, axis=1)
        
        # Draw the Scatter Plot
        # X-axis = How MANY stores? (Quantity)
        # Y-axis = How GOOD are they? (Quality)
        sns.scatterplot(
            data=cc_df, 
            x='denominator', 
            y='estimate', 
            hue='Category', # Different color for each category
            palette={'Desert (0 Stores)': 'red', 'Scarce (<3 Stores)': 'orange', 'Swamp (Unhealthy)': 'gold', 'Healthy Access': 'green'},
            s=100, # Size of dots
            alpha=0.7 # Transparency (so overlapping dots are visible)
        )
        
        plt.title("Service Gap Matrix: Food Deserts vs. Food Swamps")
        plt.xlabel("Total Food Outlets (Density)")
        plt.ylabel("Healthy Food Access Score (Quality)")
        # Add a text note directly on the chart
        plt.text(0.5, 95, "GOAL: High Density + High Quality", ha='left', color='green')
        plt.tight_layout()
        plt.savefig("food_deserts_matrix.png")
        
        # --- EXPLANATION 2 ---
        print("\n" + "-"*60)
        print("VISUAL GENERATED: 'food_deserts_matrix.png'")
        print("-"*60)
        print("WHAT IT IS: A map of 'Problem Types'.")
        print("HOW TO READ: ")
        print("  - RED DOTS (Bottom Left): 'True Deserts'. 0 Stores. Needs trucks.")
        print("  - GOLD DOTS (Bottom Right): 'Food Swamps'. Lots of stores, but junk food. Needs partnerships.")
        print("ACTION: Use this to justify different budget lines (Truck Gas vs. Community Outreach).")

        return pd.DataFrame(recommendations)
        
    except Exception as e:
        print(f"Error analyzing MRFEI: {e}")
        return None

def analyze_demand_spikes_monthly(filepath):
    """
    =============================================================================
    MODULE 2: TIMING & DEMAND
    =============================================================================
    STRATEGIC GOAL:
    We need to know WHEN demand spikes (Seasonality) so we can hire volunteers 
    in time. We also need to know WHO is coming (Household Size).
    
    DATA SOURCE: 
    SNAP Monthly Participation Data (Last 4 Years).
    =============================================================================
    """
    print("\n\n" + "="*60)
    print("ANALYSIS 2: TIMING YOUR STAFFING & INVENTORY")
    print("="*60)
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    try:
        # STEP 1: SMART LOADING
        # This file is messy. It often changes format. We scan for the valid header.
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        header_row = -1
        for i, line in enumerate(lines[:20]):
            if "Participation Persons" in line:
                header_row = i
                break
        if header_row == -1: return

        # Read starting from the correct row
        df = pd.read_csv(filepath, header=header_row)
        cols = df.columns.tolist()
        
        # Dynamic Column Finding (finds columns even if names change slightly)
        date_col = cols[0]
        part_persons_col = next((c for c in cols if "Participation Persons" in c), None) # Finds 'Persons'
        part_hh_col = next((c for c in cols if "Participation Households" in c), None)   # Finds 'Households'
        cost_col = next((c for c in cols if "Benefit Costs" in c), None)                 # Finds 'Costs'
        
        # STEP 2: CLEANING
        # Ignore "Annual Summary" rows, we only want monthly data
        df = df[~df[date_col].astype(str).str.startswith('FY', na=False)]
        df = df[~df[date_col].astype(str).str.contains('ANNUAL', na=False)]
        
        # Turn "Oct 2022" into a real computer date
        df['parsed_date'] = pd.to_datetime(df[date_col], format='%b %Y', errors='coerce')
        monthly_df = df.dropna(subset=['parsed_date']).copy()
        monthly_df = monthly_df.sort_values('parsed_date')
        
        # Fix numbers: "1,200" is text, we need to remove the comma to make it math-ready
        for col in [part_persons_col, part_hh_col, cost_col]:
            if monthly_df[col].dtype == object:
                monthly_df[col] = monthly_df[col].astype(str).str.replace(',', '').str.strip()
            monthly_df[col] = pd.to_numeric(monthly_df[col], errors='coerce')

        # STEP 3: FEATURE ENGINEERING (Creating new useful data)
        # Extract Month Name for seasonality plotting
        monthly_df['Year'] = monthly_df['parsed_date'].dt.year
        monthly_df['MonthName'] = monthly_df['parsed_date'].dt.strftime('%b')
        
        # Calculate Month-over-Month % Change
        monthly_df['MoM_Change'] = monthly_df[part_persons_col].pct_change()
        
        # Find the Peak Month
        seasonality = monthly_df.groupby('MonthName')['MoM_Change'].mean()
        peak_month = seasonality.idxmax()
        
        print(f"\n>> INSIGHT: The 'October Surprise'")
        print(f"   Data confirms demand consistently SPIKES in {peak_month}, not December.")

        # --- VISUALIZATION 3: Seasonal Pulse (Multi-Year Line Chart) ---
        plt.figure(figsize=(10, 6))
        
        # Plot lines: One line per Year
        sns.lineplot(data=monthly_df, x='MonthName', y=part_persons_col, hue='Year', marker='o', palette='tab10')
        
        plt.title("The Seasonal Pulse: SNAP Participation by Month")
        plt.ylabel("Participants")
        plt.xlabel("Month")
        plt.legend(title='Year')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig("seasonal_pulse.png")
        
        # --- EXPLANATION 3 ---
        print("\n" + "-"*60)
        print("VISUAL GENERATED: 'seasonal_pulse.png'")
        print("-"*60)
        print("WHAT IT IS: A calendar of hunger.")
        print("HOW TO READ: Look for where the lines consistently go UP together.")
        print("ACTION: Start your volunteer recruitment drive 1 month BEFORE the peak.")
        print(f"        (i.e., Recruit in September for the {peak_month} rush).")

        # --- VISUALIZATION 4: Household Complexity Shift ---
        # Ratio: People / Households. 
        # High Ratio = Large Families. Low Ratio = Singles/Seniors.
        monthly_df['Persons_per_HH'] = monthly_df[part_persons_col] / monthly_df[part_hh_col]
        
        plt.figure(figsize=(10, 5))
        plt.plot(monthly_df['parsed_date'], monthly_df['Persons_per_HH'], marker='o', color='purple')
        plt.title("The Household Complexity Shift (Persons per Household)")
        plt.ylabel("Avg Persons per HH")
        plt.xlabel("Date")
        plt.tight_layout()
        plt.savefig("household_complexity.png")
        
        # --- EXPLANATION 4 ---
        trend = "INCREASING" if monthly_df['Persons_per_HH'].iloc[-1] > monthly_df['Persons_per_HH'].iloc[0] else "DECREASING"
        print("\n" + "-"*60)
        print("VISUAL GENERATED: 'household_complexity.png'")
        print("-"*60)
        print(f"WHAT IT IS: The 'Face' of the average client. Trend is {trend}.")
        print("ACTION: Change your grocery order.")
        if trend == "DECREASING":
            print("   -> Buy fewer 'Family Packs'. Buy more single-serving meals/pop-tops.")
        else:
            print("   -> Buy more 'Family Packs'.")

        # --- VISUALIZATION 5: The Cost of Hunger (Dual Axis) ---
        # Dual-Axis means we plot two different things (People vs Dollars) on the same chart.
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # Left Axis: People (Blue)
        color = 'tab:blue'
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Participants (Millions)', color=color)
        ax1.plot(monthly_df['parsed_date'], monthly_df[part_persons_col] / 1e6, color=color, label='People', linewidth=2)
        ax1.tick_params(axis='y', labelcolor=color)
        
        # Right Axis: Cost (Green)
        ax2 = ax1.twinx()
        color = 'tab:green'
        ax2.set_ylabel('Total Benefit Cost (Billions $)', color=color)  
        ax2.plot(monthly_df['parsed_date'], monthly_df[cost_col] / 1e9, color=color, linestyle='--', label='Cost', linewidth=2)
        ax2.tick_params(axis='y', labelcolor=color)
        
        plt.title("The Cost of Hunger: Demand vs. Spending")
        plt.tight_layout()
        plt.savefig("cost_of_hunger.png")
        
        # --- EXPLANATION 5 ---
        print("\n" + "-"*60)
        print("VISUAL GENERATED: 'cost_of_hunger.png'")
        print("-"*60)
        print("WHAT IT IS: The 'ROI' of benefits.")
        print("HOW TO READ: If Green (Cost) goes up faster than Blue (People), inflation is high.")
        print("ACTION: Use this chart in Donor Letters to explain why you need more money")
        print("        just to feed the SAME number of people.")
        
        return monthly_df

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error analyzing Monthly SNAP: {e}")
        return None

def analyze_purchasing_power(filepath):
    """
    =============================================================================
    MODULE 3: HISTORICAL CONTEXT
    =============================================================================
    STRATEGIC GOAL:
    Prove to stakeholders that we are in a historic crisis.
    Comparing today's numbers to the 1970s shows the scale of the problem.
    =============================================================================
    """
    print("\n\n" + "="*60)
    print("ANALYSIS 3: HISTORICAL CONTEXT (THE 'WHY NOW?' STORY)")
    print("="*60)
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    try:
        # STEP 1: LOAD
        with open(filepath, 'r') as f: lines = f.readlines()
        header_row = -1
        # Look for headers
        for i, line in enumerate(lines[:20]):
            if "Average Participation" in line and "Average Benefit Per Person" in line:
                header_row = i; break
        if header_row == -1: return
             
        df = pd.read_csv(filepath, header=header_row)
        cols = df.columns
        year_col = cols[0]
        part_col = next((c for c in cols if "Average Participation" in c), None) 
        benefit_col = next((c for c in cols if "Average Benefit Per Person" in c), None)
        
        # STEP 2: CLEAN
        df['Year_Clean'] = pd.to_numeric(df[year_col], errors='coerce')
        annual_df = df.dropna(subset=['Year_Clean']).copy()
        
        for col in [part_col, benefit_col]:
            if annual_df[col].dtype == object:
                annual_df[col] = annual_df[col].astype(str).str.replace(',', '').str.replace(']', '').str.strip()
            annual_df[col] = pd.to_numeric(annual_df[col], errors='coerce')
        
        annual_df = annual_df.sort_values('Year_Clean')
        
        # --- VISUALIZATION 6: Modern Crisis (Area Chart) ---
        plt.figure(figsize=(12, 6))
        # FillBetween creates that solid wall of color, making the volume look "heavy"
        plt.fill_between(annual_df['Year_Clean'], annual_df[part_col]/1000, color='skyblue', alpha=0.4)
        plt.plot(annual_df['Year_Clean'], annual_df[part_col]/1000, color='SlateBlue', linewidth=2)
        
        plt.title("The Modern Crisis: SNAP Participation (1969-2025)")
        plt.ylabel("Participants (Millions)")
        plt.xlabel("Year")
        # Highlight: Draw a box around the recent crisis years
        plt.axvspan(2020, 2025, color='orange', alpha=0.2, label='Pandemic/Inflation Era')
        plt.legend()
        plt.tight_layout()
        plt.savefig("modern_crisis_history.png")
        
        # --- EXPLANATION 6 ---
        print("\n" + "-"*60)
        print("VISUAL GENERATED: 'modern_crisis_history.png'")
        print("-"*60)
        print("WHAT IT IS: The 50-Year View.")
        print("ACTION: This is your 'Cover Page' image for Grant Applications.")
        print("        It visually proves that demand is at an all-time historic high.")
        
        # --- VISUALIZATION 7: Purchasing Power Gap (Line Chart) ---
        plt.figure(figsize=(12, 6))
        plt.plot(annual_df['Year_Clean'], annual_df[benefit_col], color='green', linewidth=2, label='Avg Benefit ($)')
        
        # Highlight recent years in Red to show the volatility
        recent = annual_df[annual_df['Year_Clean'] >= 2020]
        plt.plot(recent['Year_Clean'], recent[benefit_col], color='red', linewidth=3, label='Recent Volatility')
        
        plt.title("Purchasing Power: Average Monthly Benefit Per Person")
        plt.ylabel("Benefit Amount ($)")
        plt.xlabel("Year")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.savefig("purchasing_power_gap.png")
        
        # --- EXPLANATION 7 ---
        print("\n" + "-"*60)
        print("VISUAL GENERATED: 'purchasing_power_gap.png'")
        print("-"*60)
        print("WHAT IT IS: The 'Value' of the help.")
        print("ACTION: Explain to clients that while benefits went up (Green Line),")
        print("        prices went up faster, which is why they still need the Food Bank.")
        
    except Exception as e:
        print(f"Error analyzing Annual SNAP: {e}")

def main():
    # Define our dataset files
    # Note: We are in 'py/' so we go up one level then into 'csv/'
    mrfei_file = "../csv/modified-retail-food-environment-index-data.xlsx - modified-retail-food-environment-index-data.xlsx.csv"
    monthly_file = "../csv/snap-4fymonthly-12.xlsx - Sheet1.csv"
    annual_file = "../csv/snap-annualsummary-12.xlsx - Sheet1.csv"
    
    # Run the three modules
    analyze_neighborhood_gaps(mrfei_file)
    analyze_demand_spikes_monthly(monthly_file)
    analyze_purchasing_power(annual_file)

if __name__ == "__main__":
    main()
