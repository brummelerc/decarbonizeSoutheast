#importing necessary libraries
import pandas as pd
import geopandas as gpd
import ipywidgets as widgets
from IPython.display import display

#importing Complete SEDS dataset from a downloaded file
raw_seds = pd.read_csv(r'\\vhb.com\temp\VDI\cbrummeler\decarbonizeSE\Complete_SEDS.csv')
print(raw_seds.head)

#pulling csv file from EPA website
url = 'https://www.eia.gov/state/seds/CDF/Complete_SEDS.csv'
response = requests.get(url)
csv_content = response.text

#importing data from csv file
data = StringIO(csv_content)
raw_seds = pd.read_csv(data)
print(raw_seds)

#extracting only the data for 2022 from the full SEDS dataset
seds_2022 = raw_seds[raw_seds['Year'] == 2022] #defining only the data from 2022
pivot_seds2022 = seds_2022.pivot(index = "StateCode", columns = "MSN", values = "Data") #pivoting the data so that each MSN code is a column
pivot_seds2022.index.name = 'STUSPS' #changing the index field name from StateCode to STUSPS, to match the column to the index column on the shapefile it will be joined to
print(pivot_seds2022)

#exporting 2022 SEDS dataset to csv
pivot_seds2022.to_csv(r'\\vhb.com\temp\VDI\cbrummeler\decarbonizeSE\SEDS2022.csv')

#importing shapefile of states
states_2022 = gpd.read_file(r'\\vhb.com\temp\VDI\cbrummeler\decarbonizeSE\tl_2023_us_state.shp')

#merging 2022 SEDS dataset with shapefiles
seds_states2022 = states_2022.merge(pivot_seds2022, on = 'STUSPS')

#exporting merged shapefile
seds_states2022.to_file(r'\\vhb.com\temp\VDI\cbrummeler\decarbonizeSE\seds_states2022.shp')

#creating an interactive map using the shapefile with the SEDS dataset attached
seds_states2022.explore()

#creating an interactive map using the shapefile, but displaying data based on a single column
seds_states2022.explore(
    column = "SOEGB",
    tooltip = "SOEGB",
    popup = True,
    cmap = "YlOrRd",
    tiles = "CartoDB positron")

#making the interactive map

#setting up the dropdown widget
column_dropdown = widgets.Dropdown(
    options = seds_states2022.columns,
    description = "MSN")

#defining an output widget
output = widgets.Output()

#making a method to update the interactive map when the column is changed
def update_map(column):
    output.clear_output(wait = True)
    map = seds_states2022.explore(
        column = column, 
        cmap = "YlOrRd",
        tooltip = column,
        popup = True)
    display(map)
    
#setting up the widget interaction
widgets.interact(update_map, column = column_dropdown)

#setting up the widget display
display(column_dropdown, output)

#creating a dictionary of dataframes by year
years = raw_seds['Year'].unique()

yearly_dfs = {}

for year in years:
    seds_year = raw_seds[raw_seds['Year'] == year]
    pivot_seds_year = seds_year.pivot(index = "StateCode",
                                     columns = "MSN",
                                     values = "Data")
    pivot_seds_year.index.name = "STUSPS"
    
    yearly_dfs[year] = pivot_seds_year
    
    print(f"Data for Year {year}:\n", pivot_seds_year, "\n")

#joining yearly datasets to state shapefiles to create a dictionary of
#shapefiles with a year od SEDS data attached to each
seds_stateshapes = {}

for year, pivot_df in yearly_dfs.items():
    seds_joinshapes = states_2022.join(pivot_df, on = "STUSPS", how = 'left')
    seds_stateshapes[year] = seds_joinshapes

#calling a sample year dataset
seds_stateshapes[2000].explore(
    column = "SOEGB",
    tooltip = "SOEGB",
    popup = True,
    cmap = "YlOrRd",
    tiles = "CartoDB positron")

#creating a method to make an interactive map
def create_map(year, column):
    #select the dataframe for the given year
    gdf = seds_stateshapes[year]
    
    #initialize Folium map
    m = folium.Map(location = [37.8, -96], zoom_start = 4)
    
    #create chloropleth map
    Choropleth(
        geo_data = gdf,
        name = 'choropleth',
        data = gdf,
        columns = ['STUSPS', column],
        key_on = 'feature.properties.STUSPS',
        fill_color = 'YlOrRd',
        fill_opacity = 0.7,
        line_opacity = 0.2,
        legend_name = column
    ).add_to(m)
    
    #add LayerControl to switch layers on and off
    folium.LayerControl().add_to(m)
    
    #display map
    return m

#define the years and columns available for selection
years = list(seds_stateshapes.keys())
sample_gdf = next(iter(seds_stateshapes.values()))
columns = sample_gdf.columns.difference(['geometry', 'STUSPS', 'StateCode'])

#create dropdown widgets
year_dropdown = widgets.Dropdown(option = years, description = 'Year: ')
column_dropdown = widgets.Dropdown(option = columns, description = 'Column: ')

#use 'interact' to update the map based on selections
interact(create_map, year = year_dropdown, column = column_dropdown)