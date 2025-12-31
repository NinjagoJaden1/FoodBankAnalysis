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

### Expanded Code Logic (Data Processing)
We calculate this by filtering the raw dataset for the exact conditions of a "Food Desert":
1.  **Filter by County**: `df['county_name'] == 'Contra Costa'`
2.  **Filter by Type**: `df['geotype'] == 'CT'` (Census Tracts only)
3.  **The Diagnosis Loop**:
    ```python
    # We loop through every single neighborhood
    for index, row in df.iterrows():
        total_stores = row['denominator']
        healthy_stores = row['numerator']
        
        # LOGIC: If there are ZERO stores of any kind, it's a Desert.
        if total_stores == 0:
            diagnosis = "FOOD DESERT"
            priority = "HIGH"
    ```

### Technical Implementation (How we drew the map)
Since we didn't have a GPS shapefile, we used a creative "Image Overlay" technique in Python:
*   **Library**: `matplotlib.image` + `seaborn`
*   **Technique**:
    1.  We loaded a JPG map of the county as the "Background Layer" (`plt.imshow`).
    2.  We manually defined the approximate lat/lon coordinates for our targets.
    3.  We plotted the 14 "Red Dots" as a scatter plot **on top** of the image (`zorder=10` ensures they sit above the map).
    4.  We added white outlines to the text labels (`path_effects.withStroke`) so they are readable against the busy map background.

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

### Expanded Code Logic
We created a custom function `categorize(row)` and applied it to the dataframe to create a new column called `Category`.
```python
def categorize(row):
    # Logic 1: Absolute lack of infrastructure
    if row['denominator'] == 0: 
        return 'Desert (Needs Truck)'
        
    # Logic 2: Infrastructure exists, but quality is poor
    if row['estimate'] < 10:    
        return 'Swamp (Needs Partnership)'
        
    return 'Healthy Access'

# We apply this logic to every single row
df['Category'] = df.apply(categorize, axis=1)
```

### Technical Implementation (How we drew the chart)
*   **Library**: `seaborn`
*   **Function**: `sns.scatterplot()`
*   **Key Feature**: `hue='Category'`. This argument automatically colors the dots based on the column we created above. We then used a custom `palette` dictionary to force "Deserts" to be Red and "Swamps" to be Gold, ensuring the visual matches our strategic urgency.

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

### Expanded Code Logic
We needed to prove that the spike happens *every* year, not just once.
```python
# 1. Extract the "Month Name" from the date (e.g., "2023-10-01" -> "Oct")
df['MonthName'] = df['Date'].dt.strftime('%b')

# 2. Calculate the % change from the previous month
df['MoM_Change'] = df['Participants'].pct_change()

# 3. Average this change across all 4 years to find the "Typical Year"
seasonality = df.groupby('MonthName')['MoM_Change'].mean()
peak_month = seasonality.idxmax() # The computer tells us: 'Oct'
```

### Technical Implementation (How we drew the chart)
*   **Library**: `seaborn`
*   **Function**: `sns.lineplot()`
*   **Key Feature**: `hue='Year'`. By mapping the "Year" column to the color (hue), Seaborn automatically draws 4 separate lines (one for 2021, 2022, etc.) on the same chart. This allows us to visually compare year-over-year patterns and confirm that the "October Spike" is a repeating phenomenon.

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

### Expanded Code Logic
We derived a new metric from two separate columns to create an "Efficiency Ratio".
```python
# Column A: Total Participants (Individual Humans)
# Column B: Total Households (Family Units)

# The Math: People divided by Households
df['Persons_per_HH'] = df['Participants'] / df['Households']

# Insight: If Participants went up, but Households went up FASTER, 
# then this ratio goes DOWN.
```

### Technical Implementation (How we drew the chart)
*   **Library**: `matplotlib.pyplot`
*   **Function**: `plt.plot()`
*   **Key Feature**: A simple time-series line chart. We added `marker='o'` to show the specific data points for each month, making it clear that this is concrete monthly data, not a smoothed trend line.

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

### Expanded Code Logic
We needed to compare "Millions" (People) vs "Billions" (Dollars). If we put them on the same axis, the "People" line would be a flat line at the bottom because Billions dwarfs Millions.
```python
# We access the "Benefit Costs" column and the "Participation" column
cost = df['Benefit Costs']
people = df['Participation Persons']

# We notice that Cost is growing WAY faster than People
inflation_gap = cost.pct_change() - people.pct_change()
```

### Technical Implementation (How we drew the chart)
*   **Library**: `matplotlib`
*   **Key Feature**: **Dual Axis (`twinx`)**.
    1.  We created the main axis (`ax1`) for People (Blue).
    2.  We created a "Twin" axis (`ax2 = ax1.twinx()`) that shares the same X-Axis (Date) but has an independent Y-Axis on the right side for Dollars (Green).
    3.  This allows us to overlay the two trends perfectly to show the divergence.

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

### Expanded Code Logic
We loaded a completely different dataset (`annual_summary.csv`) that goes back to 1969.
```python
# We clean the 'Year' column to ensure it interprets "1969" as a number, not text.
df['Year_Clean'] = pd.to_numeric(df['Year'])

# We filter out any empty rows or summary footers
df = df.dropna(subset=['Year_Clean'])
```

### Technical Implementation (How we drew the chart)
*   **Library**: `matplotlib`
*   **Function**: `plt.fill_between()`
*   **Key Feature**: Instead of a simple line, we used `fill_between` to color the area under the curve (`color='skyblue'`).
*   **Design Choice**: This was intentional. A solid "Wall of Blue" psychologically feels heavier and more significant than a thin line, visually reinforcing the concept of "Volume" and "Crisis".

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

### Expanded Code Logic
We wanted to highlight *just* the last few years to draw the eye to the COVID/Inflation era.
```python
# 1. Plot the whole history in Green
plt.plot(df['Year'], df['Benefit'], color='green')

# 2. Create a "subset" of data for just 2020-2024
recent_crisis = df[df['Year'] >= 2020]

# 3. Plot that subset ON TOP of the green line, but in Red
plt.plot(recent_crisis['Year'], recent_crisis['Benefit'], color='red')
```

### Technical Implementation (How we drew the chart)
*   **Library**: `matplotlib`
*   **Key Feature**: **Layering**. By calling `plt.plot` twice on the same figure, we layered the "Red Line" exactly on top of the "Green Line".
*   **Design Choice**: We made the Red line thicker (`linewidth=3`) to make it pop out as the "Danger Zone" segment of the history.
