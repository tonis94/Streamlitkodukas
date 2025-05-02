import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt

# ---------------------------
# CONSTANTS
# ---------------------------
STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_FILE = "maakonnad.geojson"

JSON_PAYLOAD_STR = """{
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": ["2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"]
      }
    },
    {
      "code": "Maakond",
      "selection": {
        "filter": "item",
        "values": ["39", "44", "49", "51", "57", "59", "65", "67", "70", "74", "78", "82", "84", "86"]
      }
    },
    {
      "code": "Sugu",
      "selection": {
        "filter": "item",
        "values": ["2", "3"]
      }
    }
  ],
  "response": {
    "format": "csv"
  }
}"""

# ---------------------------
# FUNCTIONS
# ---------------------------
@st.cache_data
def import_data():
    headers = {'Content-Type': 'application/json'}
    parsed_payload = json.loads(JSON_PAYLOAD_STR)
    response = requests.post(STATISTIKAAMETI_API_URL, json=parsed_payload, headers=headers)
    
    if response.status_code == 200:
        text = response.content.decode('utf-8-sig')
        df = pd.read_csv(StringIO(text))
        return df
    else:
        st.error(f"API error: {response.status_code}")
        return pd.DataFrame()

@st.cache_data
def import_geojson():
    return gpd.read_file(GEOJSON_FILE)

def plot_map(df_merged, year):
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    df_merged.plot(column='Loomulik iive', 
                   ax=ax,
                   legend=True,
                   cmap='viridis',
                   legend_kwds={'label': "Loomulik iive"})
    plt.title(f'Loomulik iive maakonniti aastal {year}')
    plt.axis('off')
    st.pyplot(fig)

# ---------------------------
# STREAMLIT APP
# ---------------------------
st.set_page_config(page_title="Sündimus ja suremus Eestis", layout="wide")

st.title("Sündimus ja suremus Eestis")
st.write("Tere tulemast Tõnis Reiniku Eesti iibe dashboardile!")

# Sidebar filter
selected_year = st.sidebar.selectbox("Vali aasta", list(map(str, range(2014, 2024))), index=9)

# Load data
df = import_data()
geo_df = import_geojson()

if not df.empty:
    # Filter by selected year
    year_data = df[df['Aasta'] == int(selected_year)].copy()

    # Sum male and female values for births, deaths, and natural increase
    year_data['Elussünnid'] = year_data['Mehed Elussünnid'] + year_data['Naised Elussünnid']
    year_data['Surmad'] = year_data['Mehed Surmad'] + year_data['Naised Surmad']
    year_data['Loomulik iive'] = year_data['Mehed Loomulik iive'] + year_data['Naised Loomulik iive']

    # Merge with GeoJSON
    df_merged = geo_df.merge(year_data, left_on="MNIMI", right_on="Maakond")

    # Show table
    st.subheader(f"Loomulik iive maakonniti ({selected_year})")
    st.dataframe(year_data[["Maakond", "Elussünnid", "Surmad", "Loomulik iive"]])

    # Show map
    plot_map(df_merged, selected_year)
else:
    st.warning("Andmeid ei õnnestunud laadida.")
