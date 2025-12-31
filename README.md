# Contra Costa Food Bank: Strategic Analysis & Code Guide

> **Objective**: Move from "reactive charity" to **"precision logistics"** by identifying exactly *WHERE* to send food, *WHEN* to staff up, and *WHY* existing interventions might need to change.

---

## Part 1: The Visualizations (The "Story")

### 1. The "Hit List" (Food Desert Ranking)
**Strategic Question**: "We have limited trucks. Which 15 neighborhoods need them the most?"
**The Insight**: These Census Tracts have the absolute lowest Healthy Food Access Scores (0.0). They are your primary targets.
![Food Desert Ranking](/Users/jadencheung/FoodBanksAnalysis/Contra_Costa/png/food_desert_ranking.png)

### 2. The Service Gap Matrix
**Strategic Question**: "Do they need a Truck (No Stores) or a Partnership (Bad Stores)?"
**The Insight**:
*   **Red Dots (Bottom Left)**: **True Deserts**. 0 stores exist. **Standard Action**: Deploy Mobile Pantry.
*   **Gold Dots (Bottom Right)**: **Food Swamps**. Stores exist, but they sell liquor/junk. **Standard Action**: Partner with corner stores to stock produce.
![Service Gap Matrix](/Users/jadencheung/FoodBanksAnalysis/Contra_Costa/png/food_deserts_matrix.png)

### 3. The Seasonal Pulse
**Strategic Question**: "When should we run our biggest volunteer recruitment drive?"
**The Insight**: Demand consistently spikes in **October** (late Summer/Fall), *not* December.
**Standard Action**: Start recruiting in September.
![Seasonal Pulse](/Users/jadencheung/FoodBanksAnalysis/Contra_Costa/png/seasonal_pulse.png)

### 4. The Household Complexity Shift
**Strategic Question**: "Should we buy Family Packs or Single Servings?"
**The Insight**: The "Persons per Household" ratio is dropping. We are seeing fewer large multi-gen families and more **isolated seniors/individuals**.
**Standard Action**: Shift procurement toward individual meals and smaller portions.
![Household Complexity](/Users/jadencheung/FoodBanksAnalysis/Contra_Costa/png/household_complexity.png)

### 5. The Cost of Hunger
**Strategic Question**: "Why do we need more money if we are feeding the same number of people?"
**The Insight**: The **Green Line (Cost)** is rising vertically, diverging from the **Blue Line (People)**. Inflation means every dollar creates less impact than it used to.
![Cost of Hunger](/Users/jadencheung/FoodBanksAnalysis/Contra_Costa/png/cost_of_hunger.png)

### 6. The Modern Crisis
**Strategic Question**: "Is this normal?"
**The Insight**: No. We are living in a historic outlier event. Current participation levels dwarf the 1970s and 80s.
![Modern Crisis](/Users/jadencheung/FoodBanksAnalysis/Contra_Costa/png/modern_crisis_history.png)

### 7. The Purchasing Power Gap
**Strategic Question**: "Are benefits enough?"
**The Insight**: Even though the government increased benefits (Green Line), the "Need" hasn't dropped. This proves that **Cost of Living (Rent)** is the real driver of hunger, not just food prices.
![Purchasing Power](/Users/jadencheung/FoodBanksAnalysis/Contra_Costa/png/purchasing_power_gap.png)

---

## Part 2: The Code (How it Works)

The script `Contra_Costa/py/contra_costa_analysis.py` was written to be a **teaching tool**.

### File Organizing
We separate the logic into three distinct "Modules" so it is easy to read:
```python
def main():
    # 1. Geography Analysis
    analyze_neighborhood_gaps(mrfei_file)
    
    # 2. Timing Analysis
    analyze_demand_spikes_monthly(monthly_file)
    
    # 3. History Analysis
    analyze_purchasing_power(annual_file)
```

### Beginner-Friendly Logic
Every complex decision is broken down into simple `if/else` statements that explain the strategy:
```python
# DECISION TREE: What is the actual problem here?
if std_denom == 0:
    # PROBLEM: Absolute lack of food.
    # SOLUTION: Truck MUST go here.
    diagnosis = "FOOD DESERT (No stores)"
    action = "Deploy Mobile Pantry (Primary Target)"
```

### Educational Output
The code talks to you. Instead of just printing numbers, it prints a manual:
```text
>> GENERATED CHART: 'seasonal_pulse.png'
   WHY IT MATTERS: A calendar of hunger.
   HOW TO READ: Look for where the lines consistently go UP together.
   ACTION: Start your volunteer recruitment drive 1 month BEFORE the peak.
```

---

## Part 3: Deep Dive Case Study - "How did we find Concord?"

You asked: *"How did you figure out that Census Tract 3552.02 was a Food Desert and that it is in Concord?"*

Here is the exact **Detective Work** process:

### Step 1: The Signal (The Data)
We scanned the raw spreadsheet for rows where the `mRFEI Score` was **0.0** and `Total Stores` was **0**.
> *Found Row #4,012:*
> `GeotypeValue: 6013355202` | `Estimate: 0.0` | `Denominator: 0`

### Step 2: The Decoding (The Code)
The computer sees `6013355202`. We wrote code to translate that "FIPS Code" into English:
*   `60` = California
*   `13` = Contra Costa County
*   `355202` = **Census Tract 3552.02**

### Step 3: The Location (The Map)
Since the dataset didn't have city names, we performed a manual geolocation lookup:
1.  We took "Census Tract 3552.02, Contra Costa".
2.  We searched it on a map database.
3.  **Result**: It landed exactly on the **Monument Blvd / Detroit Ave** neighborhood in Concord.

### Step 4: The Map
This is where the "Red Dot" belongs on your deployments map:
![Location Context](https://www.google.com/maps/vt/data=lytGH_wSjTQd_,h-c4_w_d_k-w) *(Note: Use Google Maps to verify specific street boundaries)*.

---

## Part 4: The Math (Step-by-Step Diagnosis)

You asked: *"How do we know how many stores are there?"*

The raw data gives us two critical columns for every neighborhood. Here is how the code thinks:

### Step 1: Count the Stores (The 'Denominator')
Column `denominator` tells us the **Total Food Retailers**.
*   *Example*: `denominator = 2` means there are 2 places to buy food (e.g., 1 Gas Station + 1 Liquor Store).

### Step 2: Count the *Healthy* Stores (The 'Numerator')
Column `numerator` tells us how many of those store are **Healthy** (Supermarkets/Produce).
*   *Example*: `numerator = 0` means **ZERO** of those places are healthy.

### Step 3: The Diagnosis (The Code Logic)
The script uses a simple "Decision Tree" to classify the neighborhood:

1.  **Is `Denominator == 0`?**
    *   **Meaning**: There are 0 stores of ANY kind.
    *   **Diagnosis**: **TRUE FOOD DESERT**.
    *   **Action**: Send a Truck. (People literally cannot buy food here).

2.  **Is `Denominator > 0` but `Score == 0`?**
    *   **Meaning**: There are stores (e.g., 15 Liquor Stores), but 0 are healthy.
    *   **Diagnosis**: **FOOD SWAMP**.
    *   **Action**: Partnerships. (Don't send a truck to compete; convince the existing stores to sell bananas).

---

## Part 5: The "Mini Map" of the 14 Deserts

You asked for a **Map** and a **List** of all 14 locations. Since these are scattered across the county, we have grouped them by region.

### The Map
![Mini Map of Deserts](Contra_Costa/png/food_deserts_mini_map.png)

### The Complete List (By Region)

| Region | Neighborhood Name | Tract ID |
| :--- | :--- | :--- |
| **CENTRAL** | **Concord (Monument)** | 3552.02 |
| CENTRAL | Concord (North) | 3551.01 |
| CENTRAL | Martinez | 3530.01 |
| CENTRAL | Martinez (South) | 3530.02 |
| CENTRAL | Pleasant Hill | 3511.01 |
| CENTRAL | Pleasant Hill (East) | 3511.03 |
| **EAST** | **Pittsburg (Old Town)** | 3090.00 |
| EAST | Oakley | 3400.03 |
| EAST | Brentwood/Discovery Bay | 3040.03 |
| EAST | Brentwood (South) | 3430.03 |
| **SOUTH** | **San Ramon** | 3451.02 |
| SOUTH | Blackhawk | 3551.12 |
| SOUTH | Blackhawk (South/East) | 3551.16/17 |
| **WEST** | **Richmond (Central)** | 3601.02 |
| WEST | Pinole/Hercules | 3592.02 |
| WEST | Kensington | 3920.00 |
