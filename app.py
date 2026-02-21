import streamlit as st
import polars as pl
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config( page_title='NYC Taxi Dashboard', page_icon='taxi', layout='wide' ) 

st.title('NYC Taxi Trip Dashboard')

@st.cache_data 
def load_data():
    try:
        df = pl.read_parquet('data/cleaned_trips.parquet')
    except FileNotFoundError:
         st.error("Can't find the dataset! Make sure 'taxi_data.parquet' is in the dashboard folder.")
         st.stop()
    df = df.sample(n=min(100000, len(df)), seed=42)
    return df 

zones_df = pl.read_csv('data/taxi_zone_lookup.csv')
df = load_data()

st.title("NYC Yellow Taxi Trip Analysis")
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
    .groupby("PULocationID")
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
st.write("The busiest pickup zones are concentrated in high-traffic Manhattan areas.")

# 2. LineChart: Avg fare by hour
avg_fare_by_hour = (
    df
    .groupby("pickup_hour")             
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
    .groupby("payment_type")  
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
    .groupby(["pickup_day_of_week", "pickup_hour"])
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