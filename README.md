# Contra Costa Food Bank: Strategic Analysis & Code Guide

> **Objective**: Move from "reactive charity" to **"precision logistics"** by identifying exactly *WHERE* to send food, *WHEN* to staff up, and *WHY* existing interventions might need to change.

---

## 1. The "Hit List" (Food Deserts Map)

### What Question does this answer?
"We have limited trucks. Which 15 neighborhoods need them the most?"

### Why it Helps
It prevents wasteful driving. It identifies the 14 specific census tracts that have **zero** healthy food access, allowing you to route your expensive Mobile Pantry trucks with surgical precision.

### How to Read this Visualization
*   **The Map**: Shows Contra Costa County.
*   **The Dots**: Each **Red Dot** is a confirmed "Food Desert" (a neighborhood with 0 healthy stores).
*   **Grouping**: The dots are clustered by region (West, Central, East, South) to help you plan truck routes.

### The Visualization
![Food Deserts Map](Contra_Costa/png/food_deserts_mini_map.png)

### The Strategy (The List)
| Region | Neighborhood Name | Priority |
| :--- | :--- | :--- |
| **CENTRAL** | Concord (Monument), Martinez, Pleasant Hill | **HIGH** |
| **EAST** | Pittsburg (Old Town), Oakley, Brentwood | **HIGH** |
| **WEST** | Richmond (Central), Pinole, Kensington | **HIGH** |
| **SOUTH** | San Ramon, Blackhawk | LOW (High Income) |

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

### What Question does this answer?
"Do they need a Truck (No Stores) or a Partnership (Bad Stores)?"

### Why it Helps
It saves money. Running a truck is expensive; signing a partnership is cheap. You shouldn't send a truck to a place that just needs a corner store intervention.

### How to Read this Visualization
*   **X-Axis (Quantity)**: How many stores are there?
*   **Y-Axis (Quality)**: How healthy are they?
*   **Red Dots (Bottom Left)**: 0 Stores. **True Desert**. -> **Send Truck**.
*   **Gold Dots (Bottom Right)**: Many Stores, but Score is 0. **Food Swamp**. -> **Partnership**.

### The Visualization
![Service Gap Matrix](Contra_Costa/png/food_deserts_matrix.png)

### The Code Logic
The scatter plot separates problems by Quantity vs Quality.
```python
def categorize(row):
    if row['denominator'] == 0: return 'Desert (Needs Truck)'
    if row['estimate'] < 10:    return 'Swamp (Needs Partnership)'
    return 'Healthy Access'
```

---

## 3. The Seasonal Pulse

### What Question does this answer?
"When should we run our biggest volunteer recruitment drive?"

### Why it Helps
It prevents labor shortages. Most people intuitively think hunger peaks at Christmas (December), but the data proves it actually peaks in **October**.

### How to Read this Visualization
*   **X-Axis**: Months of the year (Jan-Dec).
*   **Y-Axis**: Number of Participants.
*   **Trend**: Look for the consistent "Spike" in **October** (Oct) across every colored line (Year).

### The Visualization
![Seasonal Pulse](Contra_Costa/png/seasonal_pulse.png)

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

### What Question does this answer?
"Should we buy Family Packs or Single Servings?"

### Why it Helps
It optimizies inventory. Buying bulk family packs is wasteful if most of your clients are now isolated seniors living alone.

### How to Read this Visualization
*   **The Line**: Tracks "average persons per household".
*   **Falling Line**: Families are getting **smaller** (More singles/seniors).
*   **Rising Line**: Families are getting **larger**.

### The Visualization
![Household Complexity](Contra_Costa/png/household_complexity.png)

### The Code Logic
We divide the total people by the total households to see the "Average Family Size".
```python
# Ratio: People / Households
df['Persons_per_HH'] = df['Participants'] / df['Households']

# If this line goes DOWN, families are getting SMALLER.
```

---

## 5. The Cost of Hunger

### What Question does this answer?
"Why do we need more money if we are feeding the same number of people?"

### Why it Helps
It justifies fundraising asks. It visually proves that **Inflation** is increasing your costs even if your client count stays flat.

### How to Read this Visualization
*   **Blue Line (Left Axis)**: Number of People.
*   **Green Line (Right Axis)**: Cost in Dollars.
*   **The Gap**: Notice how the Green line shoots up vertically while the Blue line stays relatively flat. That gap is Inflation.

### The Visualization
![Cost of Hunger](Contra_Costa/png/cost_of_hunger.png)

### The Code Logic
We use a "Dual Axis" chart to compare two different scales (Millions of People vs Billions of Dollars).
```python
ax1.plot(df['Date'], df['People'], color='blue')  # Left Axis
ax2.plot(df['Date'], df['Cost'],   color='green') # Right Axis
```

---

## 6. The Modern Crisis

### What Question does this answer?
"Is this normal?"

### Why it Helps
It proves urgency to donors and government. It shows that the current crisis is a historic outlier, not "business as usual."

### How to Read this Visualization
*   **X-Axis**: A 50-year timeline (1970s - Present).
*   **Blue Area**: The volume of people needing help.
*   **The Wall**: The massive surge on the far right shows the unprecedented scale of today's hunger.

### The Visualization
![Modern Crisis](Contra_Costa/png/modern_crisis_history.png)

### The Code Logic
We plot raw numbers from 1969-2024 and use `fill_between` to make the area look "heavy" and overwhelming.
```python
plt.fill_between(df['Year'], df['Participants'], color='skyblue')
# This creates the "Wall of Water" effect
```

---

## 7. The Purchasing Power Gap

### What Question does this answer?
"Are government benefits enough to solve the problem?"

### Why it Helps
It shifts the focus to **Cost of Living**. It proves that even though benefits went up, people are still hungry because Rent/Inflation ate that money.

### How to Read this Visualization
*   **Green Line**: The dollar amount of benefits per person.
*   **Red Section**: Highlights the recent volatility where benefits increased but failed to solve the hunger crisis.

### The Visualization
![Purchasing Power](Contra_Costa/png/purchasing_power_gap.png)

### The Code Logic
We highlight the recent years in **Red** to show volatility.
```python
# Plot the main line in Green
plt.plot(df['Year'], df['Benefit'], color='green')

# Plot the "Pandemic Era" in Red
recent = df[df['Year'] >= 2020]
plt.plot(recent['Year'], recent['Benefit'], color='red', linewidth=3)
```
