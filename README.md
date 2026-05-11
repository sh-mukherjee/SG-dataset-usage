# Singapore Open Data Usage Analytics Dashboard

A professional, executive-level analytics dashboard built with Streamlit, Plotly, and Pandas to analyze dataset usage metrics from Singapore's open data portal.

## Features

* Executive KPI Suite: Total Views, Downloads, API Queries, and Subscriptions with calculated deltas.

* Interactive Visualizations: Time-series trends, Agency heatmaps, Format distribution, and Pareto charts.

* Advanced Metrics: Custom-engineered scores for Popularity, Engagement, and API Intensity.

* Data Exploration: Fully searchable and sortable data table with export capabilities.

* Responsive Design: Clean, modern UI suitable for various screen sizes.

## Installation

1. Clone or download this project.

2. Install the required dependencies:

pip install -r requirements.txt


3. Ensure the dataset sgdatasetusagemetrics.csv is in the root directory.

## Running the Dashboard

Execute the following command in your terminal:

streamlit run app.py


## File Structure

* app.py: The main entry point and single-file application logic.

* requirements.txt: List of Python dependencies.

* sgdatasetusagemetrics.csv: Source dataset.

## Troubleshooting

* Missing Columns: The app includes a dynamic mapper to detect column variations (e.g., managed_by_agency vs agency).

* Data Loading: Uses @st.cache_data for high performance during interactive filtering.
