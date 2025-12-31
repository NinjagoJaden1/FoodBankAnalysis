# Contra Costa Food Bank: Strategic Analysis & Code Guide

> **Objective**: Move from "reactive charity" to **"precision logistics"** by identifying exactly *WHERE* to send food, *WHEN* to staff up, and *WHY* existing interventions might need to change.

---

## 1. The "Hit List" (Food Deserts Map)
**Strategic Question**: "We have limited trucks. Which 15 neighborhoods need them the most?"
**The Insight**: These Census Tracts have the absolute lowest Healthy Food Access Scores (0.0). They are your primary targets.

### The Visualization
![Food Deserts Map](Contra_Costa/png/food_deserts_mini_map.png)

### The Strategy (The List)
| Region | Neighborhood Name (Tract) | Priority |
| :--- | :--- | :--- |
| **CENTRAL** | **Concord (Monument Blvd)** | HIGH |
| CENTRAL | Martinez & Pleasant Hill | MEDIUM |
| **EAST** | **Pittsburg (Old Town)** | HIGH |
| EAST | Oakley & Brentwood | MEDIUM |
| **SOUTH** | **San Ramon & Blackhawk** | LOW (High Income) |
| **WEST** | **Richmond (Central)** | HIGH |

### The Code Logic (How we built this)
We didn't just guess. The script finds these specific locations using a "Decision Tree":
1.  **Count Stores** (`denominator`): "How many places sell food?"
2.  **Count Quality** (`numerator`): "How many of them are supermarkets?"
3.  **The Diagnosis**:
    ```python
    if denominator == 0:
        diagnosis = "FOOD DESERT (No stores)"
        action = "Deploy Mobile Pantry (Primary Target)"
    ```

---

## 2. The Service Gap Matrix
**Strategic Question**: "Do they need a Truck (No Stores) or a Partnership (Bad Stores)?"
**The Insight**: Not all hunger is the same. Some areas need *food* (Desert), others need *better food* (Swamp).

### The Visualization
![Service Gap Matrix](Contra_Costa/png/food_deserts_matrix.png)

### The Strategy
*   **Red Dots (Bottom Left) = Deserts**: 0 stores exist. Truck required.
*   **Gold Dots (Bottom Right) = Swamps**: Stores exist, but they sell liquor/junk. **Solution**: Partner with them to stock bananas/produce instead of sending a competing truck.

### The Code Logic
The scatter plot separates problems by **Quantity** (X-Axis) vs **Quality** (Y-Axis).
```python
def categorize(row):
    if row['denominator'] == 0: return 'Desert (Needs Truck)'
    if row['estimate'] < 10:    return 'Swamp (Needs Partnership)'
    return 'Healthy Access'
```

---

## 3. The Seasonal Pulse
**Strategic Question**: "When should we run our biggest volunteer recruitment drive?"
**The Insight**: Demand consistently spikes in **October** (late Summer/Fall), *not* December.

### The Visualization
![Seasonal Pulse](Contra_Costa/png/seasonal_pulse.png)

### The Strategy
*   **Myth**: "Hunger peaks at Christmas."
*   **Reality**: Hunger peaks in October.
*   **Action**: Start recruiting volunteers in **September**.

### The Code Logic
We use `groupby` to average the demand for every month across 4 years to find the "Hidden Seasonality".
```python
# Calculate Month-over-Month % Change
df['MoM_Change'] = df['Participants'].pct_change()

# Find the Peak
seasonality = df.groupby('MonthName')['MoM_Change'].mean()
peak_month = seasonality.idxmax() # Returns 'Oct'
```

---

## 4. The Household Complexity Shift
**Strategic Question**: "Should we buy Family Packs or Single Servings?"
**The Insight**: The "Persons per Household" ratio is dropping. We are seeing fewer large multi-gen families and more **isolated seniors/individuals**.

### The Visualization
![Household Complexity](Contra_Costa/png/household_complexity.png)

### The Strategy
*   **Old Way**: "Family Box" (Pasta, Rice, Whole Chicken).
*   **New Way**: "Senior Bag" (Pop-top cans, single servings, easy prep).

### The Code Logic
We divide the total people by the total households to see the "Average Family Size".
```python
# Ratio: People / Households
df['Persons_per_HH'] = df['Participants'] / df['Households']

# If this line goes DOWN, families are getting SMALLER.
```

---

## 5. The Cost of Hunger
**Strategic Question**: "Why do we need more money if we are feeding the same number of people?"
**The Insight**: The **Green Line (Cost)** is rising vertically, diverging from the **Blue Line (People)**.

### The Visualization
![Cost of Hunger](Contra_Costa/png/cost_of_hunger.png)

### The Strategy
*   **Donor Pitch**: "We aren't serving more people; it just costs 2x more to buy the same apple."
*   **Proof**: Show them the gap between the lines.

### The Code Logic
We use a "Dual Axis" chart to compare two different scales (Millions of People vs Billions of Dollars).
```python
ax1.plot(df['Date'], df['People'], color='blue')  # Left Axis
ax2.plot(df['Date'], df['Cost'],   color='green') # Right Axis
```

---

## 6. The Modern Crisis
**Strategic Question**: "Is this normal?"
**The Insight**: No. We are living in a historic outlier event. Current participation levels dwarf the 1970s and 80s.

### The Visualization
![Modern Crisis](Contra_Costa/png/modern_crisis_history.png)

### The Strategy
*   **Action**: Use this as the "Cover Page" for any Federal Grant application. It visually proves that the current system is under unprecedented stress.

### The Code Logic
We simply plotted the raw participation numbers from 1969 to 2024. The visual impact comes from using `fill_between` to make the area look "heavy" and overwhelming.
```python
plt.fill_between(df['Year'], df['Participants'], color='skyblue')
# This creates the "Wall of Water" effect
```

---

## 7. The Purchasing Power Gap
**Strategic Question**: "Are benefits enough?"
**The Insight**: Even though the government increased benefits (Green Line), the "Need" hasn't dropped.

### The Visualization
![Purchasing Power](Contra_Costa/png/purchasing_power_gap.png)

### The Strategy
*   **The Narrative**: "It's not about food prices. It's about Rent."
*   **Explanation**: If benefits represent "Food Money" and they went up, but people are still hungry, then the problem is that their "Rent Money" is eating their budget.

### The Code Logic
We highlight the recent years in **Red** to show volatility.
```python
# Plot the main line in Green
plt.plot(df['Year'], df['Benefit'], color='green')

# Plot the "Pandemic Era" in Red
recent = df[df['Year'] >= 2020]
plt.plot(recent['Year'], recent['Benefit'], color='red', linewidth=3)
```
