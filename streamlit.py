# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import requests
import zipfile
from io import BytesIO

#######################
st.set_page_config(
    page_title="Credit Card Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

st.markdown(
    """
    <h1 style='text-align: center;'>
        Credit Card Analysis
    </h1>
    """,
    unsafe_allow_html=True
)
alt.themes.enable("dark")

# Correct CSV export URL using the File ID

local_zip_file = "data.zip"

# Open the ZIP file from the local path
chunk_size = 50000  # Adjust this value based on available memory

# Initialize an empty list to store chunks
chunks = []

# Open the ZIP file from the local path
@st.cache_data
with zipfile.ZipFile(local_zip_file, 'r') as z:
    file_name = z.namelist()[0]  # Get the first file name in the ZIP archive
    with z.open(file_name) as excel_file:
        # Read the CSV file in chunks
        for chunk in pd.read_csv(excel_file, chunksize=chunk_size, low_memory=False):
            # Perform any processing on each chunk here (optional)
            chunks.append(chunk)

# Concatenate all chunks into a single DataFrame
df_reshaped = pd.concat(chunks, ignore_index=True)
# excel_file = z.open("data.zip")
# chunk_size = 50  # Adjust this based on your needs

# df_reshaped = pd.concat(df_list, ignore_index=True)

#######################
# Sidebar
with st.sidebar:
    # Step 1: Extract distinct years
    st.markdown(
    """
    <h1 style='text-align: center;'>Credit Card Analysis Dashboard</h1>
    """,
    unsafe_allow_html=True
    )
    df_reshaped['Transaction_date'] = pd.to_datetime(df_reshaped['Transaction_date'])
    distinct_years = df_reshaped['Transaction_date'].dt.year.unique()
    distinct_years = sorted(distinct_years)  # Sort the years

    # Add "All Years" option
    years_options = ['All Years'] + list(distinct_years)

    # Step 2: Add the district filter
    district_list = ['All Districts'] + list(df_reshaped['district_name'].unique())
    selected_district = st.selectbox('Select a district', district_list)

    # Step 3: Add the year filter
    selected_year = st.selectbox('Select a year', years_options)

    # Step 4: Add color theme options
    color_theme_list = ['plasma', 'cividis', 'greens', 'inferno', 'magma', 'blues', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('Select a color theme', color_theme_list)

df_filtered = df_reshaped.copy()

# Filter the DataFrame based on the selected district
if selected_district != 'All Districts':
    df_filtered = df_filtered[df_filtered['district_name'] == selected_district]

# Apply year filter
if selected_year != 'All Years':
    df_filtered = df_filtered[df_filtered['Transaction_date'].dt.year == int(selected_year)]

if selected_year != 'All Years':
    df_year_filtered = df_reshaped[df_reshaped['Transaction_date'].dt.year == int(selected_year)]
else:
    df_year_filtered = df_reshaped
df_district_counts = df_year_filtered['district_name'].value_counts().reset_index()
df_district_counts.columns = ['district_name', 'count']

# Function to create the column chart
def make_column_chart(input_df, input_y, input_x, input_color, input_color_theme):
    column_chart = alt.Chart(input_df).mark_bar().encode(
        x=alt.X(f'{input_y}:O', axis=alt.Axis(title="District", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
        y=alt.Y(f'{input_x}:Q', axis=alt.Axis(title="Customer count", titleFontSize=18, titlePadding=15, titleFontWeight=900)),
        color=alt.Color(f'{input_color}:Q',
                        legend=None,
                        scale=alt.Scale(scheme=input_color_theme)),
    ).properties(width=900).configure_axis(
        labelFontSize=12,
        titleFontSize=12
    ) 
    return column_chart


column_chart = make_column_chart(df_district_counts, input_y='district_name', input_x='count', input_color='count', input_color_theme=selected_color_theme)
# st.altair_chart(column_chart)


# # Donut chart
operation_counts = df_filtered['operation'].value_counts().reset_index()
operation_counts.columns = ['operation', 'count']

def make_donut(input_df, selected_color_theme):
    # Define chart colors based on selected_color_theme
    color_theme_list = {
        'blues': ['#08306B', '#2171B5', '#4292C6', '#6BAED6', '#9ECAE1'],
        'greens': ['#00441B', '#006D2C', '#238B45', '#41AB5D', '#74C476'],
        'orange': ['#F39C12', '#875A12', '#FAB763', '#FDC98F', '#FFE0C1'],
        'reds': ['#E74C3C', '#781F16', '#F5877E', '#F8B0AB', '#FBD7D3'],
        'cividis': ['#00204C', '#395A96', '#7A8FC6', '#BDC4E0', '#FFFFC8'],
        'inferno': ['#000004', '#420A68', '#932667', '#DD513A', '#FCA50A'],
        'magma': ['#000004', '#3B0F70', '#8C2981', '#DE4968', '#FE9F6D'],
        'plasma': ['#0D0887', '#6A00A8', '#B12A90', '#E16462', '#FCA636'],
        'rainbow': ['#E70000', '#FF8C00', '#FFD700', '#008000', '#00CED1'],
        'turbo': ['#30123B', '#456F87', '#A8D865', '#EED607', '#FA9600'],
        'viridis': ['#440154', '#3B528B', '#21918C', '#5EC962', '#FDE725'],
    }

    # Get the color scheme for the selected theme
    chart_color = color_theme_list.get(selected_color_theme, ['#333333', '#cccccc', '#888888', '#bbbbbb', '#dddddd'])  # Default colors

    # Calculate the percentage of each operation
    input_df['% value'] = 100 * (input_df['count'] / input_df['count'].sum())

    # Create the donut chart
    donut_chart = alt.Chart(input_df).mark_arc(innerRadius=80, outerRadius=120).encode(
        theta=alt.Theta(field="% value", type="quantitative"),
        color=alt.Color(field='operation', type='nominal', scale=alt.Scale(range=chart_color)),
        tooltip=[alt.Tooltip(field='operation', type='nominal'),
                 alt.Tooltip(field='% value', type='quantitative', title='Percentage')]
    ).properties(width=400, height=400)

    return donut_chart


# Generate and display the donut chart with operation counts
donut_chart = make_donut(operation_counts, selected_color_theme)
# st.altair_chart(donut_chart)


def make_bar(dataframe, column_name,selected_color_theme):
    frequency_counts = dataframe[column_name].value_counts().reset_index()
    frequency_counts.columns = [column_name, 'count']

    # Define chart colors based on selected_color_theme
    color_theme_list = {
        'blues': ['#08306B', '#2171B5', '#4292C6', '#6BAED6', '#9ECAE1'],
        'greens': ['#00441B', '#006D2C', '#238B45', '#41AB5D', '#74C476'],
        'orange': ['#F39C12', '#875A12', '#FAB763', '#FDC98F', '#FFE0C1'],
        'reds': ['#E74C3C', '#781F16', '#F5877E', '#F8B0AB', '#FBD7D3'],
        'cividis': ['#00204C', '#395A96', '#7A8FC6', '#BDC4E0', '#FFFFC8'],
        'inferno': ['#000004', '#420A68', '#932667', '#DD513A', '#FCA50A'],
        'magma': ['#000004', '#3B0F70', '#8C2981', '#DE4968', '#FE9F6D'],
        'plasma': ['#0D0887', '#6A00A8', '#B12A90', '#E16462', '#FCA636'],
        'rainbow': ['#E70000', '#FF8C00', '#FFD700', '#008000', '#00CED1'],
        'turbo': ['#30123B', '#456F87', '#A8D865', '#EED607', '#FA9600'],
        'viridis': ['#440154', '#3B528B', '#21918C', '#5EC962', '#FDE725'],
    }

    # Get the color scheme for the selected theme
    chart_color = color_theme_list.get(selected_color_theme, ['#333333', '#cccccc', '#888888', '#bbbbbb', '#dddddd'])  # Default colors

    # Create the bar chart
    chart = alt.Chart(frequency_counts).mark_bar().encode(
        x=alt.X('count:Q', title='Count'),
        y=alt.Y(f'{column_name}:N', title='Frequency', sort='-x'),
        color=alt.Color(f'{column_name}:N', title='Frequency', scale=alt.Scale(range=chart_color)),
        tooltip=[f'{column_name}:N', 'count:Q']
    ).properties(
        title=f'Number of Accounts by Frequency of Issuance',
        width=1000,  # Adjust width to fit well within the Streamlit app
        height=400  # Adjust height as needed
    ).interactive()
    
    # Show the chart in Streamlit
    return chart

# Example usage:
bar_chart = make_bar(df_filtered, 'frequency', selected_color_theme)
# try:
#     st.altair_chart(bar_chart)
# except Exception:
#     pass

def make_column_chart(dataframe, x_column, color_theme):
    # Define chart colors based on selected_color_theme
    color_theme_list = {
        'blues': ['#08306B', '#2171B5', '#4292C6', '#6BAED6', '#9ECAE1'],
        'greens': ['#00441B', '#006D2C', '#238B45', '#41AB5D', '#74C476'],
        'orange': ['#F39C12', '#875A12', '#FAB763', '#FDC98F', '#FFE0C1'],
        'reds': ['#E74C3C', '#781F16', '#F5877E', '#F8B0AB', '#FBD7D3'],
        'cividis': ['#00204C', '#395A96', '#7A8FC6', '#BDC4E0', '#FFFFC8'],
        'inferno': ['#000004', '#420A68', '#932667', '#DD513A', '#FCA50A'],
        'magma': ['#000004', '#3B0F70', '#8C2981', '#DE4968', '#FE9F6D'],
        'plasma': ['#0D0887', '#6A00A8', '#B12A90', '#E16462', '#FCA636'],
        'rainbow': ['#E70000', '#FF8C00', '#FFD700', '#008000', '#00CED1'],
        'turbo': ['#30123B', '#456F87', '#A8D865', '#EED607', '#FA9600'],
        'viridis': ['#440154', '#3B528B', '#21918C', '#5EC962', '#FDE725'],
    }

    # Get the color scheme for the selected theme
    chart_color = color_theme_list.get(color_theme, ['#333333', '#cccccc', '#888888', '#bbbbbb', '#dddddd'])  # Default colors

    # Count occurrences of each category in the x_column
    count_df = dataframe[x_column].value_counts().reset_index()
    count_df.columns = [x_column, 'count']

    Column_Name = x_column.replace('_', ' ')

    # Create the column chart
    column_chart = alt.Chart(count_df).mark_bar(color=chart_color[0]).encode(
        x=alt.X(f'{x_column}:O', title=Column_Name, axis=alt.Axis(titleFontSize=18, titlePadding=15, titleFontWeight=900)),
        y=alt.Y('count:Q', title='Count', axis=alt.Axis(titleFontSize=18, titlePadding=15, titleFontWeight=900)),
        tooltip=[alt.Tooltip(f'{x_column}:O', title=x_column),
                 alt.Tooltip('count:Q', title='Count')]
    ).properties(
        width=600,  # Adjust width to fit well within the Streamlit app
        height=400, # Adjust height as needed
        title=f'Count of Different {Column_Name}'
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    )
    
    # Show the chart in Streamlit
    return column_chart

column_2_chart = make_column_chart(df_filtered, 'transaction_type', selected_color_theme)
# st.altair_chart(column_chart)

column_1_chart = make_column_chart(df_filtered, 'Credit_card_type', selected_color_theme)
# st.altair_chart(column_1_chart)

def plot_top_districts_by_salary(dataframe, color_theme, column_district='district_name', column_salary='avg_salary', top_n=10):
    # Define chart colors based on selected_color_theme
    color_theme_list = {
        'blues': ['#08306B', '#2171B5', '#4292C6', '#6BAED6', '#9ECAE1'],
        'greens': ['#00441B', '#006D2C', '#238B45', '#41AB5D', '#74C476'],
        'orange': ['#F39C12', '#875A12', '#FAB763', '#FDC98F', '#FFE0C1'],
        'reds': ['#E74C3C', '#781F16', '#F5877E', '#F8B0AB', '#FBD7D3'],
        'cividis': ['#00204C', '#395A96', '#7A8FC6', '#BDC4E0', '#FFFFC8'],
        'inferno': ['#000004', '#420A68', '#932667', '#DD513A', '#FCA50A'],
        'magma': ['#000004', '#3B0F70', '#8C2981', '#DE4968', '#FE9F6D'],
        'plasma': ['#0D0887', '#6A00A8', '#B12A90', '#E16462', '#FCA636'],
        'rainbow': ['#E70000', '#FF8C00', '#FFD700', '#008000', '#00CED1'],
        'turbo': ['#30123B', '#456F87', '#A8D865', '#EED607', '#FA9600'],
        'viridis': ['#440154', '#3B528B', '#21918C', '#5EC962', '#FDE725'],
    }

    # Get the color scheme for the selected theme
    chart_color = color_theme_list.get(color_theme, ['#333333', '#cccccc', '#888888', '#bbbbbb', '#dddddd'])  # Default colors

    # Filter and sort the DataFrame to get the top N districts with the highest average salary
    unique_districts = dataframe.drop_duplicates(subset=['district_name'])

    top_districts = (unique_districts
                     .sort_values(by=column_salary, ascending=False)
                     .head(top_n)
                     .reset_index(drop=True))

    # Create the bar chart
    chart = alt.Chart(top_districts).mark_bar(color=chart_color[0]).encode(
        x=alt.X(f'{column_district}:N', title='District', sort='-y'),
        y=alt.Y(f'{column_salary}:Q', title='Average Salary'),
        color=alt.Color(f'{column_salary}:Q', legend=None, scale=alt.Scale(scheme=color_theme)),
        tooltip=[alt.Tooltip(f'{column_district}:N', title='District'),
                 alt.Tooltip(f'{column_salary}:Q', title='Average Salary')]
    ).properties(
        title='Top Districts with Highest Average Salary',
        width=600,
        height=400
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        fontSize=16,
        fontWeight='bold'
    )

    return chart

avg_salary_chart = plot_top_districts_by_salary(df_year_filtered, selected_color_theme)
# st.altair_chart(avg_salary_chart)


def plot_age_distribution(dataframe, color_theme, bins=20):
    # Define chart colors based on the selected color theme
    color_theme_list = {
        'blues': ['#08306B', '#2171B5', '#4292C6', '#6BAED6', '#9ECAE1'],
        'greens': ['#00441B', '#006D2C', '#238B45', '#41AB5D', '#74C476'],
        'orange': ['#F39C12', '#875A12', '#FAB763', '#FDC98F', '#FFE0C1'],
        'reds': ['#E74C3C', '#781F16', '#F5877E', '#F8B0AB', '#FBD7D3'],
        'cividis': ['#00204C', '#395A96', '#7A8FC6', '#BDC4E0', '#FFFFC8'],
        'inferno': ['#000004', '#420A68', '#932667', '#DD513A', '#FCA50A'],
        'magma': ['#000004', '#3B0F70', '#8C2981', '#DE4968', '#FE9F6D'],
        'plasma': ['#0D0887', '#6A00A8', '#B12A90', '#E16462', '#FCA636'],
        'rainbow': ['#E70000', '#FF8C00', '#FFD700', '#008000', '#00CED1'],
        'turbo': ['#30123B', '#456F87', '#A8D865', '#EED607', '#FA9600'],
        'viridis': ['#440154', '#3B528B', '#21918C', '#5EC962', '#FDE725'],
    }

    # Get the color scheme for the selected theme, default to grayscale colors if not found
    chart_color = color_theme_list.get(color_theme, ['#333333', '#cccccc', '#888888', '#bbbbbb', '#dddddd'])

    # Create the histogram chart using the selected color theme for the bars
    histogram_chart = alt.Chart(dataframe).mark_bar().encode(
        x=alt.X('age:Q', bin=alt.Bin(maxbins=bins), title='Age'),
        y=alt.Y('count:Q', title='Count'),
        color=alt.Color('count:Q', scale=alt.Scale(range=chart_color), legend=None)
    ).properties(
        title=f'Age Distribution of Customers',
        width=600,
        height=400
    )
    kde_line = alt.Chart(dataframe).transform_density(
        density='age',
        as_=['age', 'density'],
        extent=[dataframe['age'].min(), dataframe['age'].max()]
    ).mark_line(color=chart_color[0], strokeWidth=2).encode(
        x=alt.X('age:Q', title='Age'),
        y=alt.Y('density:Q')
    )

    # Layer the histogram and KDE line
    chart = alt.layer(histogram_chart, kde_line).resolve_scale(y='independent')

    return chart

# Aggregate the data before passing to the chart
df_filtered['age'] = 2024 - pd.to_datetime(df_filtered['date_of_birth']).dt.year
df_aggregated = df_filtered.groupby('age').size().reset_index(name='count')

# Plot the chart with a chosen color theme
age_chart = plot_age_distribution(df_aggregated, selected_color_theme)
# st.altair_chart(age_chart)

# Dashboard Main Panel
with st.container():
    # Big Column Chart
    st.altair_chart(column_chart, use_container_width=True)

with st.container():
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Donut Chart
        st.altair_chart(donut_chart, use_container_width=True)
    
    with col2:
        # Bar Chart
        st.altair_chart(bar_chart, use_container_width=True)

    with col3:
        st.altair_chart(avg_salary_chart, use_container_width=True)

with st.container():
    # Three Medium Column Charts
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.altair_chart(column_2_chart, use_container_width=True)
    
    with col2:
        st.altair_chart(column_1_chart, use_container_width=True)    

    with col3:
        st.altair_chart(age_chart, use_container_width=True)    
