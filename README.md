# COMP 3610 – Assignment 1  
## NYC Yellow Taxi Trips Analysis & Dashboard

This project analyzes the NYC Yellow Taxi Trip dataset using modern data engineering tools.  
It covers data ingestion, cleaning, feature engineering, analytical queries, and an interactive dashboard built with Streamlit.

---

## 📌 Project Overview

The goal of this assignment is to:
- Process and analyze large-scale trip data efficiently
- Perform feature engineering and analytical queries
- Build an interactive dashboard to explore trip patterns

The project is implemented using **Polars**, **DuckDB**, and **Streamlit**, with development and prototyping done in **Google Colab** and **VS Code**.

---

# COMP 3610 – Assignment 1  
## NYC Yellow Taxi Trips Analysis & Dashboard

This project analyzes the NYC Yellow Taxi Trip dataset using modern data engineering tools.  
It covers data ingestion, cleaning, feature engineering, analytical queries, and an interactive dashboard built with Streamlit.

---

## 📌 Project Overview

The goal of this assignment is to:
- Process and analyze large-scale trip data efficiently
- Perform feature engineering and analytical queries
- Build an interactive dashboard to explore trip patterns

The project is implemented using **Polars**, **DuckDB**, and **Streamlit**, with development and prototyping done in **Google Colab** and **VS Code**.

---

## 🧹 Data Processing

- Raw NYC Yellow Taxi trip data (~3 million rows) was cleaned and processed in a notebook.
- Data cleaning included:
  - Removing invalid timestamps and distances
  - Handling missing and inconsistent values
- Feature engineering added:
  - Trip duration (minutes)
  - Trip speed (mph)
  - Pickup hour
  - Pickup day of week

⚠️ **Note:**  
The raw dataset is **not included** in this repository.  
Only the processed dataset is stored to support analysis and dashboard functionality.

---

## 📊 Analysis & Visualizations

Five required visualizations were created:

1. **Bar Chart** – Top 10 pickup zones by trip count  
2. **Line Chart** – Average fare by hour of day  
3. **Histogram** – Distribution of trip distances  
4. **Bar Chart** – Breakdown of payment types  
5. **Heatmap** – Trips by day of week and hour  

All visualizations are driven by dynamic filters:
- Pickup date range
- Pickup hour range
- Payment type

---

## 🖥️ Interactive Dashboard

The Streamlit dashboard allows users to:
- Filter trips by date, hour, and payment type
- Explore trip patterns through interactive charts
- View aggregated insights in real time

### Run the dashboard locally:

```bash
pip install -r requirements.txt
streamlit run app.py

