import streamlit as st
import polars as pl
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config( page_title='NYC Taxi Dashboard', page_icon='taxi', layout='wide' ) 

st.title('NYC Taxi Trip Dashboard')

import requests

tripData = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
zoneLookup = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

tripDataPath = "yellow_tripdata_2024-01.parquet"
zoneLookupPath = "taxi_zone_lookup.csv"

def download_file(url, dest):
  response = requests.get(url)
  response.raise_for_status()
  with open(dest, "wb") as f:
    f.write(response.content)
  print("file downloaded")

download_file(tripData,tripDataPath)
download_file(zoneLookup, zoneLookupPath)

@st.cache_data 
def load_data():
    try:
        # First try the local copy in the dashboard folder
        lf = pl.scan_parquet('yellow_tripdata_2024-01.parquet')
    except FileNotFoundError:
        try:
            # Maybe it's in the parent directory?
            lf = pl.scan_parquet('../yellow_tripdata_2024-01.parquet')
        except FileNotFoundError:
            # Okay, we're stuck - let the user know what's up
            st.error("Can't find the dataset! Make sure 'taxi_data.parquet' is in the dashboard folder.")
            st.stop()
    
    try:
        # First try the local copy in the dashboard folder
        zones_df = pl.read_csv('taxi_zone_lookup.csv')
    except FileNotFoundError:
        try:
            # Maybe it's in the parent directory?
            zones_df = pl.read_csv('../data/taxi_zone_lookup.csv')
        except FileNotFoundError:
            # Okay, we're stuck - let the user know what's up
            st.error("Can't find the dataset! Make sure 'taxi_zone_lookup.csv' is in the dashboard folder.")
            st.stop()
            
    df = (
        lf
        .with_columns([
            pl.col("tpep_pickup_datetime").dt.hour().alias("pickup_hour"),
            pl.col("tpep_pickup_datetime").dt.weekday().alias("pickup_weekday"),
            pl.col("tpep_pickup_datetime").dt.date().alias("pickup_date"),

            (
                (pl.col("tpep_dropoff_datetime") - pl.col("tpep_pickup_datetime"))
                .dt.total_seconds() / 60
            ).alias("trip_duration_min"),

            (
                pl.when(pl.col("fare_amount") > 0)
                .then(pl.col("tip_amount") / pl.col("fare_amount") * 100)
                .otherwise(0)
            ).alias("tip_pct"),
        ])
        .filter(
            (pl.col("fare_amount") > 0) & (pl.col("fare_amount") < 200) &
            (pl.col("trip_distance") > 0) & (pl.col("trip_distance") < 50) &
            (pl.col("trip_duration_min") > 1) & (pl.col("trip_duration_min") < 180)
        )
        .filter(pl.rand(seed=42) < 0.02)  # seeded randomness
        .head(100_000)
        .collect()
    )

    return df, zones_df
    
df, zones_df = load_data()

st.write("This dashboard explores travel patterns, fares, and payment behavior in NYC taxi trips.")

# ---------------- FILTERS ----------------
st.sidebar.header("Filters")

date_range = st.sidebar.date_input(
    "Pickup Date Range",
    [df["tpep_pickup_datetime"].min().date(),
     df["tpep_pickup_datetime"].max().date()]
)

hour_range = st.sidebar.slider("Pickup Hour", 0, 23, (0, 23))

payment_types = st.sidebar.multiselect(
    "Payment Type",
    sorted(df["payment_type"].unique().to_list()),
    default=sorted(df["payment_type"].unique().to_list())
)

filtered_df = df.filter(
    (pl.col("tpep_pickup_datetime").dt.date().is_between(date_range[0], date_range[1])) &
    (pl.col("pickup_hour").is_between(hour_range[0], hour_range[1])) &
    (pl.col("payment_type").is_in(payment_types))
)

# ---------------- METRICS ----------------
st.subheader("Key Metrics")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Trips", filtered_df.height)
col2.metric("Avg Fare ($)", round(filtered_df["fare_amount"].mean(), 2))
col3.metric("Total Revenue ($)", round(filtered_df["total_amount"].sum(), 2))
col4.metric("Avg Distance (mi)", round(filtered_df["trip_distance"].mean(), 2))
col5.metric("Avg Duration (min)", round(filtered_df["trip_duration_minutes"].mean(), 2))

# ---------------- VISUALS ----------------
st.subheader("Visualizations")

# 1. Barchart: Top pickup zones

top_pickups = (
    df
    .group_by("PULocationID")
    .agg(pl.count().alias("trip_count")) 
    .sort("trip_count", descending=True)
    .head(10)
    .join(zones_df, left_on="PULocationID", right_on="LocationID")
)

fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(
    top_pickups["Zone"].to_list(),
    top_pickups["trip_count"].to_list(),
    color="skyblue",
    edgecolor="black"
)
ax.set_xlabel("Number of Trips")
ax.set_title("Top 10 Pickup Zones by Trip Count")
ax.invert_yaxis()  

st.pyplot(fig)

# 2. LineChart: Avg fare by hour
avg_fare_by_hour = (
    df
    .group_by("pickup_hour")             
    .agg(pl.col("fare_amount").mean().alias("avg_fare"))
    .sort("pickup_hour")
)

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(
    avg_fare_by_hour["pickup_hour"].to_list(),
    avg_fare_by_hour["avg_fare"].to_list(),
    marker="o",
    color="skyblue"
)
ax.set_xlabel("Hour of Day")
ax.set_ylabel("Average Fare ($)")
ax.set_title("Average Fare by Hour of Day")
ax.grid(True)

st.pyplot(fig)

st.write("Fares increase during peak commuting hours, reflecting demand patterns.")

# 3. Histogram: Trip distance distribution

fig, ax = plt.subplots(figsize=(8, 4))
ax.hist(
    df["trip_distance"].to_list(), 
    bins=40,  
    color="skyblue", 
    edgecolor="black"
)
ax.set_xlabel("Trip Distance (miles)")
ax.set_ylabel("Number of Trips")
ax.set_title("Distribution of Trip Distances")

st.pyplot(fig)
st.write("Most trips are short-distance, with a long tail of longer journeys.")

# 4. Barchart: Payment type breakdown
payment_counts = (
    df
    .group_by("payment_type")  
    .agg(pl.count().alias("count"))  
    .sort("payment_type")
)

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(
    payment_counts["payment_type"].to_list(),
    payment_counts["count"].to_list(),
    color="skyblue" 
)

ax.set_xlabel("Payment Type")
ax.set_ylabel("Number of Trips")
ax.set_title("Breakdown of Payment Types")

st.pyplot(fig)

# 5. Heatmap: Trips by day of week and hour
heatmap_df = (
    df
    .group_by(["pickup_day_of_week", "pickup_hour"])
    .agg(pl.count().alias("trip_count"))
    .sort(["pickup_day_of_week", "pickup_hour"])
)

heatmap_pivot = heatmap_df.pivot(
    values="trip_count",
    index="pickup_day_of_week",
    on="pickup_hour"
).fill_null(0)

heatmap_matrix = heatmap_pivot.drop("pickup_day_of_week").to_numpy().astype(float)

fig, ax = plt.subplots(figsize=(12, 5))
cax = ax.imshow(heatmap_matrix, aspect="auto", cmap="viridis")
fig.colorbar(cax, label="Number of Trips")

# Set x-axis (hours)
ax.set_xticks(np.arange(0, 24))
ax.set_xticklabels(np.arange(0, 24))
ax.set_xlabel("Hour of Day")

# Set y-axis (days)
weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
ax.set_yticks(np.arange(0, 7))
ax.set_yticklabels(weekdays)
ax.set_ylabel("Day of Week")

ax.set_title("Trips by Day of Week and Hour")

st.pyplot(fig)
st.write("Taxi demand peaks during weekday mornings and evenings.")