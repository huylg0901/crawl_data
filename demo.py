from geopy.distance import geodesic
import geopy
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def generate_circle_points(center_lat, center_lon, radius_km, num_points=100):
    # Create a list of angles to calculate coordinates around the center
    angles = np.linspace(0, 360, num_points)
    origin = geopy.Point(center_lat, center_lon)
    circle_points = []
    for angle in angles:
        # Calculate point coordinates based on angle and radius
        point = geodesic(kilometers=radius_km).destination(origin, angle)
        circle_points.append((point.latitude, point.longitude))
    return circle_points

def plot_map_with_circle(df, center_lat, center_lon, radius_km):
    fig = px.scatter_mapbox(df, lat='lat', lon='lon',
                            hover_name='address', hover_data=['work_neighborhood', 'distance'],
                            color_discrete_sequence=["blue"], size_max=15, zoom=10, height=300)
    fig.update_layout(mapbox_style='open-street-map', margin={"r":0,"t":0,"l":0,"b":0})
    
    # Create a circle
    circle_points = generate_circle_points(center_lat, center_lon, radius_km)
    lat_points, lon_points = zip(*circle_points)
    
    # Add the circle to the map
    fig.add_trace(go.Scattermapbox(lat=lat_points, lon=lon_points, mode='lines',
                                   line=dict(width=2, color='blue'), name='Radius'))
    
    return fig

def filter_points_by_radius(df, center_lat, center_lon, radius_km):
    center = (center_lat, center_lon)
    def within_radius(row):
        if pd.isna(row['lat']) or pd.isna(row['lon']):
            return False
        point = (row['lat'], row['lon'])
        return geodesic(center, point).km <= radius_km
    
    filtered_df = df[df.apply(within_radius, axis=1)]
    filtered_df['distance'] = filtered_df.apply(lambda row: geodesic(center, (row['lat'], row['lon'])).km, axis=1)
    return filtered_df

def main():
    st.title('Map Visualization with Distance Calculations')
    
    st.markdown("""
                <style>
                    button.step-up {display: none;}
                    button.step-down {display: none;}
                    div[data-baseweb] {border-radius: 4px;}
                </style>""",
                unsafe_allow_html=True)
    
    # Sidebar: Input and file selection
    with st.sidebar:
        provinces_to_files = {
        "Biên Hòa": "output_bienhoa_edit.xlsx",
        }
        selected_province = st.selectbox('Select a Province', list(provinces_to_files.keys()), index=None,placeholder="Select Province",)
        if selected_province:  
            selected_file = provinces_to_files[selected_province]
        else:
            selected_file = None
        center_lat = st.number_input('Enter Latitude',value=None, format="%.6f", placeholder="Enter Latitude")
        center_lon = st.number_input('Enter Longitude',value=None, format="%.6f", placeholder="Enter Longitude")
        radius_km = st.number_input('Select Radius in Km', min_value=0, value=None, format="%d", placeholder="Enter Km")
    
    # Main area: Map display
    if selected_file:
        df = pd.read_excel(selected_file)
        df = df.dropna(subset=['lat', 'lon'])

        if st.sidebar.button('Display Points within Radius and Circle'):
            filtered_df = filter_points_by_radius(df, center_lat, center_lon, radius_km)
            fig = plot_map_with_circle(filtered_df, center_lat, center_lon, radius_km)
            st.plotly_chart(fig)
            st.write("Filtered Points within the Specified Radius:")
            st.dataframe(filtered_df[['address', 'distance']])  # Display the DataFrame in the Streamlit app
            

if __name__ == "__main__":
    main()
