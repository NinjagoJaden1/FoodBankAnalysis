
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import matplotlib.image as mpimg
import matplotlib.patheffects as PathEffects

def generate_map():
    # Load the User's Map to use as background
    # We will plot "Red Dots" on top of this image.
    map_img_path = "../png/Contra-Costa-County-Map-California.jpg"
    try:
        img = mpimg.imread(map_img_path)
    except FileNotFoundError:
        print(f"Error: Could not find map image at {map_img_path}")
        return

    # --- COORDINATE CALIBRATION SYSTEM ---
    # Since the image is just a picture (not a GPS file), we have to guess
    # where the cities are using "Pixel Coordinates" or "Relative Coordinates".
    #
    # We assume the map is roughly:
    # Left edge (West): -122.45
    # Right edge (East): -121.50
    # Bottom edge (South): 37.70
    # Top edge (North): 38.10
    
    deserts = [
        # WEST COUNTY
        {'Name': 'Kensington', 'Region': 'West Bay', 'Lon': -122.27, 'Lat': 37.90},
        {'Name': 'Richmond (Ctrl)', 'Region': 'West Bay', 'Lon': -122.34, 'Lat': 37.93},
        {'Name': 'Pinole/Hercules', 'Region': 'West Bay', 'Lon': -122.29, 'Lat': 38.00},
        
        # CENTRAL COUNTY
        {'Name': 'Martinez', 'Region': 'Central', 'Lon': -122.13, 'Lat': 38.01},
        {'Name': 'Martinez (South)', 'Region': 'Central', 'Lon': -122.12, 'Lat': 37.99},
        {'Name': 'Concord (North)', 'Region': 'Central', 'Lon': -122.03, 'Lat': 38.00},
        {'Name': 'Concord (Monument)', 'Region': 'Central', 'Lon': -122.03, 'Lat': 37.96},
        {'Name': 'Pleasant Hill', 'Region': 'Central', 'Lon': -122.06, 'Lat': 37.94},
        {'Name': 'Pleasant Hill (E)', 'Region': 'Central', 'Lon': -122.05, 'Lat': 37.93},

        # SOUTH COUNTY
        {'Name': 'San Ramon', 'Region': 'South', 'Lon': -121.97, 'Lat': 37.77},
        {'Name': 'Blackhawk', 'Region': 'South', 'Lon': -121.91, 'Lat': 37.81},
        {'Name': 'Blackhawk (S)', 'Region': 'South', 'Lon': -121.90, 'Lat': 37.79},
        {'Name': 'Blackhawk (E)', 'Region': 'South', 'Lon': -121.89, 'Lat': 37.80},

        # EAST COUNTY
        {'Name': 'Pittsburg', 'Region': 'East', 'Lon': -121.88, 'Lat': 38.02},
        {'Name': 'Oakley', 'Region': 'East', 'Lon': -121.71, 'Lat': 38.00},
        {'Name': 'Brentwood', 'Region': 'East', 'Lon': -121.69, 'Lat': 37.93},
        {'Name': 'Brentwood (S)', 'Region': 'East', 'Lon': -121.70, 'Lat': 37.91},
    ]
    
    df = pd.DataFrame(deserts)
    
    # Plot Size should match the aspect ratio of your image roughly
    plt.figure(figsize=(14, 10))
    
    # Show the Map Image
    # 'extent' defines the [Left, Right, Bottom, Top] boundaries in coordinates
    # We fine-tune these numbers until the dots land on the right cities
    extent = [-122.45, -121.50, 37.70, 38.10] 
    plt.imshow(img, extent=extent, aspect='auto', alpha=0.6) # alpha makes map slightly faded so dots pop
    
    # Plot the Red Dots
    sns.scatterplot(
        data=df, 
        x='Lon', y='Lat', 
        hue='Region', 
        s=200, 
        edgecolor='black',
        palette='tab10'
    )
    
    # Add Text Labels
    for i, row in df.iterrows():
        plt.text(
            row['Lon'], row['Lat'] + 0.005, 
            row['Name'], 
            horizontalalignment='center',
            color='black',
            weight='bold',
            fontsize=10,
            path_effects=[PathEffects.withStroke(linewidth=3, foreground="white")]
        )

    plt.title("Food Deserts Overlay: Contra Costa County", fontsize=16)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    
    output_path = "../png/food_deserts_mini_map.png"
    plt.savefig(output_path)
    print(f"Map updated: {output_path}")

if __name__ == "__main__":
    generate_map()
