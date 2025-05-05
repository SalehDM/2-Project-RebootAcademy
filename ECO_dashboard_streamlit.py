import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
import time
import pydeck as pdk
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- PAGE SETUP ---
st.set_page_config(page_title="CO2 Emissions Dashboard", layout="wide")

# --- COLORS ---
COLOR_PRIMARY = "#1c3e6d"
COLOR_ACCENT = "#f49828"
COLOR_GREEN = "#37a387"
COLOR_GREEN_LIGHT = "#71b85e"
COLOR_YELLOW = "#fad12f"
COLOR_BG = "#f5f8fa"

# --- CUSTOM STYLE ---
st.markdown(f"""
    <style>
        .main {{
            background-color: {COLOR_BG};
            color: {COLOR_PRIMARY};
        }}
        .sidebar .sidebar-content {{
            background-color: {COLOR_PRIMARY};
            color: {COLOR_PRIMARY};
        }}
        .css-1d391kg {{
            color: {COLOR_PRIMARY};
        }}
        h2, h1, h3, .stMarkdown p, .stText, .stTitle {{
            color: {COLOR_PRIMARY};
        }}
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 0rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }}
        .element-container {{
            margin-bottom: 0.5rem !important;
        }}
        iframe {{
            height: 300px !important;
        }}
    </style>
""", unsafe_allow_html=True)

# --- SIDE MENU ---
#logo in optional menu: st.sidebar.image("rebooteco_logo.png", width=140)
st.sidebar.title("CO2 Emissions Dashboard")
page = st.sidebar.radio("Content", [
    "Global Trend",
    "Events and Impacts",
    "CO₂-Temperature Relationship",
    "Emissions by Region",
    "Responsible Sectors"
])

# --- Load data ---
@st.cache_data
def load_data():
    return pd.read_csv("dataset_visualizacion_co2.csv")

df = load_data()

# --- GLOBAL YEAR SLIDER ---
st.sidebar.markdown("---")
selected_year = st.sidebar.slider("Select year", min_value=1850, max_value=2025, value=2020)

# --- LOGO PER PAGE ---
st.image("rebooteco_logo.png", width=200)

# --- TITLES PER PAGE AND GRAPHICS ---
if page == "Global Trend":
    st.title("How has the global trend in CO₂ emissions evolved?")
    df_world = df[df['territory'] == 'World']
    df_world_filtered = df_world[df_world['year'] <= selected_year]

    df_world_co2 = df_world_filtered[['year', 'cement_co2', 'co2', 'co2_including_luc', 'coal_co2', 'flaring_co2', 'gas_co2', 'oil_co2', 'land_use_change_co2']]
    df_melted = df_world_co2.melt(id_vars=['year'], var_name='Segmento', value_name='Emisiones de CO₂(MtCO₂)')

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Line by emission source")
        fig1 = px.line(df_melted, x="year", y="Emisiones de CO₂(MtCO₂)", color='Segmento', title='Emisiones globales por fuente')
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Comparison: Total vs Including LUC")
        fig2 = px.area(df_world_filtered, x='year', y=['co2', 'co2_including_luc'], title='CO₂ total vs con cambio de uso de tierra')
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Bar Chart by Sector for Selected Year")
        df_year = df_world_filtered[df_world_filtered['year'] == selected_year]
        df_bar = df_year[['cement_co2', 'coal_co2', 'flaring_co2', 'gas_co2', 'oil_co2', 'land_use_change_co2']].sum().reset_index()
        df_bar.columns = ['Sector', 'Emissions']
        fig3 = px.bar(df_bar, x='Sector', y='Emissions', title=f'Emissions by Sector in {selected_year}')
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("Cumulative Emissions")
        df_world_filtered['cumulative'] = df_world_filtered['co2'].cumsum()
        fig4 = px.line(df_world_filtered, x='year', y='cumulative', title='Historical Cumulative CO₂ Emissions')
        st.plotly_chart(fig4, use_container_width=True)

elif page == "Events and Impacts":
        st.title("What periods show significant changes and what events influenced them?")

        # Create decade column and calculate aggregates
        df["decade"] = (df["year"] // 10) * 10
        df_decade = df.groupby("decade")[["co2"]].sum().reset_index()
        df_decade["co2_growth_prct"] = df_decade["co2"].pct_change() * 100

        # Key events aligned with actual peaks
        updated_events = {
        1860: "First Industrial Revolution",
        1910: "World War I",
        1940: "World War II",
        1970: "Oil Crisis",
        1990: "Fall of the USSR",
        2020: "COVID-19"
        }

        # Create interactive figure with secondary Y-axis
        import plotly.graph_objects as go

        fig = go.Figure()

        # Emissions line (primary Y-axis)
        fig.add_trace(go.Scatter(
        x=df_decade["decade"],
        y=df_decade["co2"],
        mode="lines+markers",
        name="CO₂ Emissions",
        line=dict(color=COLOR_PRIMARY, width=3),
        yaxis="y"
        ))

        # Growth percentage line (secondary Y-axis)
        fig.add_trace(go.Scatter(
        x=df_decade["decade"],
        y=df_decade["co2_growth_prct"],
        mode="lines+markers",
        name="% Growth",
        line=dict(color=COLOR_ACCENT, width=2, dash="dash"),
        yaxis="y2"
        ))

        # Annotations
        for year, label in updated_events.items():
            if year in df_decade["decade"].values:
                y_val = df_decade[df_decade["decade"] == year]["co2"].values[0]
                fig.add_annotation(
                x=year,
                y=y_val,
                text=label,
                showarrow=True,
                arrowhead=1,
                ax=20,
                ay=-40,
                font=dict(size=10),
                arrowcolor="gray"
                )

        # Layout with two Y-axes
        fig.update_layout(
        title="Evolution of CO₂ Emissions and Key Events by Decade",
        xaxis_title="Decade",
        yaxis=dict(
            title="Emissions (Mt)",
            titlefont=dict(color=COLOR_PRIMARY),
            tickfont=dict(color=COLOR_PRIMARY)
        ),
        yaxis2=dict(
            title="% Growth",
            overlaying="y",
            side="right",
            showgrid=False,
            titlefont=dict(color=COLOR_ACCENT),
            tickfont=dict(color=COLOR_ACCENT)
        ),
        template="plotly_white",
        font=dict(color=COLOR_PRIMARY),
        legend=dict(orientation="h", y=-0.2)
        )

        # Display first row
        st.subheader("Emissions by Decade with Historical Events")
        st.plotly_chart(fig, use_container_width=True)

        # Second row: historical cumulative
        st.subheader("Historical Cumulative Emissions up to the Selected Year")
        df_world = df[df['territory'] == 'World']
        df_world_filtered = df_world[df_world['year'] <= selected_year]
        df_world_filtered['cumulative'] = df_world_filtered['co2'].cumsum()
        fig2 = px.area(df_world_filtered, x='year', y='cumulative',
               title='Cumulative CO₂ Over Time',
               color_discrete_sequence=[COLOR_PRIMARY])
        st.plotly_chart(fig2, use_container_width=True)


elif page == "CO₂-Temperature Relationship":
    st.title("Is there a relationship between CO₂ emissions and temperature increase?")
    df_world = df[df['territory'] == 'World']

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Temperature Change by Gas")
        df_world_temp = df_world[['year', 'temperature_change_from_ch4', 'temperature_change_from_co2', 'temperature_change_from_ghg', 'temperature_change_from_n2o']]
        df_temp_melted = df_world_temp.melt(id_vars=['year'], var_name='gas_type', value_name='temperature_change')
        fig1 = px.line(df_temp_melted, x="year", y="temperature_change", color='gas_type', title='Temperature Change by Gas')
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Total CO₂ Emissions")
        fig2 = px.area(df_world, x='year', y='co2', title='Global CO₂ Emissions')
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("CO₂ vs Temperature Comparison")
        df_compare = df_world[['year', 'co2', 'temperature_change_from_ghg']].dropna()
        fig3 = px.line(df_compare, x='year', y=['co2', 'temperature_change_from_ghg'], title='CO₂ and Temperature Relationship')
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("CO₂ vs Temperature Scatter")
        fig4 = px.scatter(df_compare, x='co2', y='temperature_change_from_ghg', trendline='ols', title='CO₂ vs Temperature')
        st.plotly_chart(fig4, use_container_width=True)


elif page == "CO₂-Temperature Relationship":
    st.title("Is there a relationship between CO₂ emissions and temperature increase?")
    df_world = df[df['territory'] == 'World']

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Temperature Change by Gas")
        df_world_temp = df_world[['year', 'temperature_change_from_ch4', 'temperature_change_from_co2', 'temperature_change_from_ghg', 'temperature_change_from_n2o']]
        df_temp_melted = df_world_temp.melt(id_vars=['year'], var_name='gas_type', value_name='temperature_change')
        fig1 = px.line(df_temp_melted, x="year", y="temperature_change", color='gas_type', title='Temperature Change by Gas')
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Total CO₂ Emissions")
        fig2 = px.area(df_world, x='year', y='co2', title='Global CO₂ Emissions')
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("CO₂ vs Temperature Comparison")
        df_compare = df_world[['year', 'co2', 'temperature_change_from_ghg']].dropna()
        fig3 = px.line(df_compare, x='year', y=['co2', 'temperature_change_from_ghg'], title='CO₂ and Temperature Relationship')
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("CO₂ vs Temperature Scatter")
        fig4 = px.scatter(df_compare, x='co2', y='temperature_change_from_ghg', trendline='ols', title='CO₂ vs Temperature')
        st.plotly_chart(fig4, use_container_width=True)

elif page == "Emissions by Region":
    st.title("Which continents are the biggest emitters?")
    df = pd.read_csv('dataset_visualizacion_co2.csv')
    # Primera fila: gráfica de barras ocupa toda la fila
    st.subheader("CO₂ Emissions by Continent Over Decades")
    df_continent = df[df['continent'] != 'Unknown'].groupby(["decade", "continent"], as_index=False)["co2_including_luc"].sum()
    fig1 = px.bar(df_continent,
                  x="decade",
                  y="co2_including_luc",
                  color="continent",
                  title="CO₂ Emissions by Continent Over Decades",
                  color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig1, use_container_width=True)

    # Segunda fila: dos columnas
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("CO₂ Emissions by Country and Continent (Animated Map)")
        df_map = df[df['continent'] != 'Unknown'].groupby(["year", "continent", "iso_code", "territory"], as_index=False)["co2_including_luc"].sum()
        fig2 = px.scatter_geo(df_map,
                              locations="iso_code",
                              color="continent",
                              hover_name="territory",
                              size=(df_map["co2_including_luc"].abs())*2,
                              animation_frame="year",
                              projection="natural earth",
                              title="CO₂ Emissions by Country Over Time")
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.subheader("CO₂ Emissions Distribution in the 2010s")
        df_countries = df[(df['continent'] != 'Unknown') & (df['decade'] == 2010)] \
            .groupby(["continent", "iso_code", "territory"], as_index=False)["co2_including_luc"].sum()
        df_countries = df_countries[df_countries["co2_including_luc"] > 0]
        fig3 = px.sunburst(df_countries,
                           path=['continent', 'territory'],
                           values="co2_including_luc",
                           color='co2_including_luc',
                           hover_data=['iso_code'],
                           color_continuous_scale='RdBu',
                           title="CO₂ Emissions by Continent and Country (2010s)")
        st.plotly_chart(fig3, use_container_width=True)
    # Tercera fila: Global Share of CO₂ Emissions: China vs USA
    st.subheader("Global Share of CO₂ Emissions: China vs USA")
    df_chn_usa = df[df['territory'].isin(['China', 'United States'])][
            ['year', 'territory', 'share_global_co2_including_luc']]
    fig3 = px.line(df_chn_usa,
                       x="year",
                       y="share_global_co2_including_luc",
                       color='territory',
                       title="Country's Share of Global CO₂ Emissions")
    st.plotly_chart(fig3, use_container_width=True)

elif page == "Responsible Sectors":
    st.title("Which sectors are responsible for most CO₂ emissions?")
    df = pd.read_csv('dataset_visualizacion_co2.csv')
    # --- ROW 1 ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("CO₂ Emissions per GDP in the 2010s")
        df_gdp = df[(df['continent'] != 'Unknown') & (df['decade'] == 2010)] \
            .groupby(["continent", "iso_code", "territory"], as_index=False)["co2_including_luc_per_gdp"].sum()

        # Escalar los valores pequeños
        df_gdp["co2_including_luc_per_gdp"] = df_gdp["co2_including_luc_per_gdp"] * 1_000_000

        # Filtrar valores positivos y redondear
        df_gdp = df_gdp[df_gdp["co2_including_luc_per_gdp"] > 1]
        df_gdp["co2_including_luc_per_gdp"] = df_gdp["co2_including_luc_per_gdp"].round(0)

        df_gdp = df_gdp[df_gdp["co2_including_luc_per_gdp"].abs() > 1e-6]

        if df_gdp.empty:
            st.warning("No CO₂ per GDP data available for this period.")
        else:
            fig2 = px.sunburst(
                df_gdp,
                path=['continent', 'territory'],
                values="co2_including_luc_per_gdp",
                color='co2_including_luc_per_gdp',
                hover_data=['iso_code'],
                color_continuous_scale='RdBu',
                title="CO₂ Emissions per GDP (2010s)"
            )
            st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.subheader("Global Share of CO₂ Emissions: DRC vs Liberia")
        df_cod_lbr = df[df['territory'].isin(['Democratic Republic of Congo', 'Liberia'])][
            ['year', 'territory', 'share_global_co2_including_luc']]
        fig1 = px.line(df_cod_lbr,
                    x="year",
                    y="share_global_co2_including_luc",
                    color='territory',
                    title="Country's Share of Global CO₂ Emissions")
        st.plotly_chart(fig1, use_container_width=True)

    # --- ROW 2 ---
    st.subheader("CO₂ Emissions in the DRC by Source")
    df_cod = df[df['territory'] == 'Democratic Republic of Congo'][[
            'year', 'cement_co2', 'co2', 'co2_including_luc',
            'coal_co2', 'flaring_co2', 'gas_co2', 'oil_co2', 'land_use_change_co2']]
    df_melted_cod = df_cod.melt(id_vars='year',
                                    var_name='Source',
                                    value_name='CO₂ Emissions')
    fig4 = px.line(df_melted_cod,
                    x="year",
                    y="CO₂ Emissions",
                    color='Source',
                    title='DRC: CO₂ Emissions by Source')
    st.plotly_chart(fig4, use_container_width=True)

    # --- ROW 3 ---
    col5, col6 = st.columns(2)

    with col5:
        st.subheader("CO₂ Emissions in China by Source")
        df_chn = df[df['territory'] == 'China'][[
            'year', 'cement_co2', 'co2', 'co2_including_luc',
            'coal_co2', 'flaring_co2', 'gas_co2', 'oil_co2', 'land_use_change_co2']]
        df_melted_chn = df_chn.melt(id_vars='year',
                                    var_name='Source',
                                    value_name='CO₂ Emissions')
        fig5 = px.line(df_melted_chn,
                       x="year",
                       y="CO₂ Emissions",
                       color='Source',
                       title='China: CO₂ Emissions by Source')
        st.plotly_chart(fig5, use_container_width=True)

    with col6:
        st.subheader("CO₂ Emissions in the USA by Source")
        df_usa = df[df['territory'] == 'United States'][[
            'year', 'cement_co2', 'co2', 'co2_including_luc',
            'coal_co2', 'flaring_co2', 'gas_co2', 'oil_co2', 'land_use_change_co2']]
        df_melted_usa = df_usa.melt(id_vars='year',
                                    var_name='Source',
                                    value_name='CO₂ Emissions')
        fig6 = px.line(df_melted_usa,
                       x="year",
                       y="CO₂ Emissions",
                       color='Source',
                       title='USA: CO₂ Emissions by Source')
        st.plotly_chart(fig6, use_container_width=True)


st.markdown("---")
