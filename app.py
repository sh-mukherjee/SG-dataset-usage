import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(
    page_title="SG Data Insights | Executive Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THEME & STYLING ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; color: #1f77b4; }
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; white-space: pre-wrap; background-color: #ffffff; 
        border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px;
    }
    div[data-testid="stExpander"] { border: none; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# --- DATA LOADING & PREPROCESSING ---
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        
        # Dynamic Column Mapping
        column_map = {
            'id': 'dataset_id',
            'name': 'dataset_name',
            'managed_by_agency': 'agency',
            'api_query': 'api_queries'
        }
        df = df.rename(columns=column_map)
        
        # Handle Missing Categorical Data
        categorical_cols = ['quarter', 'dataset_name', 'agency', 'format']
        for col in categorical_cols:
            if col in df.columns:
                # Ensure all are strings and replace nan-like values
                df[col] = df[col].astype(str).replace(['nan', 'None', '', 'NaN'], 'Unknown')
            else:
                df[col] = 'Unknown'
        
        # Ensure core numeric columns exist
        numeric_cols = ['page_views', 'downloads', 'api_queries', 'subscriptions']
        for col in numeric_cols:
            if col not in df.columns:
                df[col] = 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        # Engineering Derived Metrics
        df['engagement_rate'] = (df['downloads'] / df['page_views']).replace([np.inf, -np.inf], 0).fillna(0)
        df['api_intensity'] = (df['api_queries'] / (df['downloads'] + 1)).fillna(0)
        
        # Popularity Score: Weighted Index
        # 40% Downloads, 30% API, 20% Views, 10% Subscriptions
        df['popularity_score'] = (
            (df['downloads'] * 0.4) + 
            (df['api_queries'] * 0.3) + 
            (df['page_views'] * 0.2) + 
            (df['subscriptions'] * 0.1)
        )
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# --- HELPER FUNCTIONS ---
def format_big_number(num):
    if num >= 1e6: return f"{num/1e6:.2f}M"
    if num >= 1e3: return f"{num/1e3:.1f}K"
    return str(int(num))

# --- MAIN APP ---
def main():
    df_raw = load_data('sgdatasetusagemetrics.csv')
    
    if df_raw.empty:
        st.warning("Please ensure 'sgdatasetusagemetrics.csv' is available in the directory.")
        return

    # --- SIDEBAR FILTERS ---
    st.sidebar.title("🔍 Global Filters")
    
    # Robust Sorting: Ensure all elements are strings before sorting to avoid TypeError
    def get_safe_sorted(series, reverse=False):
        unique_vals = [str(x) for x in series.unique()]
        # Remove 'Unknown' from the list to sort it separately or handle it
        main_list = sorted([x for x in unique_vals if x != 'Unknown'], reverse=reverse)
        if 'Unknown' in unique_vals:
            return main_list + ['Unknown']
        return main_list

    quarters = get_safe_sorted(df_raw['quarter'], reverse=True)
    selected_quarters = st.sidebar.multiselect("Select Quarters", quarters, default=quarters[:min(2, len(quarters))])
    
    agencies = get_safe_sorted(df_raw['agency'])
    selected_agencies = st.sidebar.multiselect("Select Agencies", agencies)
    
    formats = get_safe_sorted(df_raw['format'])
    selected_formats = st.sidebar.multiselect("Data Formats", formats)
    
    search_query = st.sidebar.text_input("Search Dataset Name", "")

    # Filtering Logic
    df = df_raw.copy()
    if selected_quarters:
        df = df[df['quarter'].isin(selected_quarters)]
    if selected_agencies:
        df = df[df['agency'].isin(selected_agencies)]
    if selected_formats:
        df = df[df['format'].isin(selected_formats)]
    if search_query:
        df = df[df['dataset_name'].str.contains(search_query, case=False)]

    # --- TOP HEADER ---
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.title("Singapore Open Data Usage")
        st.markdown(f"**Analyzing {len(df['dataset_id'].unique())} datasets across {len(df['agency'].unique())} agencies.**")
    with col_t2:
        st.write("") # Spacer
        st.download_button(
            label="📊 Export Filtered Data",
            data=df.to_csv(index=False),
            file_name=f"sg_data_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    # --- NAVIGATION TABS ---
    tab1, tab2, tab3 = st.tabs(["📈 Executive Overview", "🏢 Agency & Dataset Deep Dive", "🔬 Behavioural Insights"])

    # --- PAGE 1: EXECUTIVE OVERVIEW ---
    with tab1:
        # KPI Row
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        
        with kpi1:
            st.metric("Total Views", format_big_number(df['page_views'].sum()))
        with kpi2:
            st.metric("Total Downloads", format_big_number(df['downloads'].sum()))
        with kpi3:
            st.metric("API Queries", format_big_number(df['api_queries'].sum()))
        with kpi4:
            st.metric("Subscriptions", format_big_number(df['subscriptions'].sum()))
        with kpi5:
            st.metric("Avg Popularity", round(df['popularity_score'].mean(), 1))

        st.markdown("---")
        
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader("Usage Trends Over Time")
            metric_to_plot = st.selectbox("Select Trend Metric", 
                                       ["page_views", "downloads", "api_queries", "subscriptions"], 
                                       key="trend_sel")
            
            trend_df = df_raw.groupby('quarter')[metric_to_plot].sum().reset_index()
            # Ensure categorical type for string quarters to avoid string sorting issues in plot
            trend_df = trend_df[trend_df['quarter'] != 'Unknown'].sort_values('quarter')
            
            fig_trend = px.line(trend_df, x='quarter', y=metric_to_plot, 
                                markers=True, template="plotly_white",
                                color_discrete_sequence=['#1f77b4'])
            fig_trend.update_layout(hovermode="x unified", margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig_trend, use_container_width=True)

        with c2:
            st.subheader("Format Distribution")
            format_agg = df.groupby('format')['page_views'].sum().reset_index()
            fig_pie = px.pie(format_agg, values='page_views', names='format', 
                            hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_layout(margin=dict(l=0, r=0, t=20, b=0), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("Top 10 Datasets by Impact")
        impact_metric = st.segmented_control("Primary Metric", 
                                          options=["popularity_score", "downloads", "api_queries", "page_views"],
                                          default="popularity_score")
        
        top_10 = df.groupby('dataset_name')[impact_metric].sum().nlargest(10).reset_index()
        fig_bar = px.bar(top_10, x=impact_metric, y='dataset_name', orientation='h',
                        color=impact_metric, color_continuous_scale='Blues')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- PAGE 2: DATASET & AGENCY ANALYSIS ---
    with tab2:
        st.subheader("Agency Performance Heatmap")
        agency_pivot = df.groupby('agency')[['page_views', 'downloads', 'api_queries', 'subscriptions']].sum()
        
        if not agency_pivot.empty:
            # Scale for visualization
            agency_pivot_norm = (agency_pivot - agency_pivot.min()) / (agency_pivot.max() - agency_pivot.min() + 1e-9)
            
            fig_heat = px.imshow(agency_pivot_norm.head(20), 
                                labels=dict(x="Metric", y="Agency", color="Relative Intensity"),
                                color_continuous_scale="Viridis")
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("No agency data available for the current selection.")

        st.markdown("---")
        
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            st.subheader("API vs Download Correlation")
            fig_scatter = px.scatter(df, x="downloads", y="api_queries", 
                                   size="page_views", color="format",
                                   hover_name="dataset_name", log_x=True, log_y=True,
                                   template="plotly_white", title="Consumption Patterns (Log Scale)")
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        with col_s2:
            st.subheader("Pareto Analysis (Downloads)")
            pareto_df = df.groupby('dataset_name')['downloads'].sum().sort_values(ascending=False).reset_index()
            total_dl = pareto_df['downloads'].sum()
            if total_dl > 0:
                pareto_df['cumulative_perc'] = 100 * pareto_df['downloads'].cumsum() / total_dl
                
                fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
                fig_pareto.add_trace(go.Bar(x=pareto_df['dataset_name'][:15], y=pareto_df['downloads'][:15], name="Downloads"), secondary_y=False)
                fig_pareto.add_trace(go.Scatter(x=pareto_df['dataset_name'][:15], y=pareto_df['cumulative_perc'][:15], name="Cumulative %", line=dict(color='red')), secondary_y=True)
                fig_pareto.update_layout(title="Top 15 Datasets Cumulative Impact", showlegend=False)
                st.plotly_chart(fig_pareto, use_container_width=True)
            else:
                st.info("No download data for Pareto analysis.")

        st.subheader("Complete Dataset Metrics")
        st.dataframe(
            df[['dataset_name', 'agency', 'format', 'page_views', 'downloads', 'api_queries', 'popularity_score']]
            .sort_values('popularity_score', ascending=False),
            use_container_width=True,
            hide_index=True
        )

    # --- PAGE 3: BEHAVIOURAL INSIGHTS ---
    with tab3:
        st.subheader("Engagement & Efficiency Metrics")
        
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.write("**High Engagement (Downloads/View)**")
            st.write("Measures how often a view leads to a successful download.")
            top_eng = df[df['page_views'] > 100].nlargest(5, 'engagement_rate')[['dataset_name', 'engagement_rate']]
            st.table(top_eng)
            
        with m_col2:
            st.write("**API Intensity (API/Download)**")
            st.write("Identifies datasets predominantly consumed via automation.")
            top_api = df[df['downloads'] > 10].nlargest(5, 'api_intensity')[['dataset_name', 'api_intensity']]
            st.table(top_api)

        with m_col3:
            st.write("**Correlation Matrix**")
            corr_cols = ['page_views', 'downloads', 'api_queries', 'subscriptions']
            corr = df[corr_cols].corr()
            fig_corr = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r")
            fig_corr.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_corr, use_container_width=True)

        st.subheader("Agency Content Flow")
        # Sankey Data preparation
        sankey_df = df.groupby(['agency', 'format'])['downloads'].sum().reset_index()
        sankey_df = sankey_df[sankey_df['downloads'] > 0].nlargest(20, 'downloads')
        
        if not sankey_df.empty:
            # Map labels to indices
            all_nodes = list(set(sankey_df['agency']) | set(sankey_df['format']))
            node_map = {node: i for i, node in enumerate(all_nodes)}
            
            fig_sankey = go.Figure(data=[go.Sankey(
                node = dict(pad = 15, thickness = 20, line = dict(color = "black", width = 0.5), label = all_nodes),
                link = dict(
                    source = [node_map[a] for a in sankey_df['agency']],
                    target = [node_map[f] for f in sankey_df['format']],
                    value = sankey_df['downloads']
                )
            )])
            fig_sankey.update_layout(title_text="Volume Flow: Agency → Format", font_size=10)
            st.plotly_chart(fig_sankey, use_container_width=True)
        else:
            st.info("No usage volume to display flow.")

if __name__ == "__main__":
    main()