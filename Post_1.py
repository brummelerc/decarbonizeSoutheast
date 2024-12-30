import pandas as pd
import geopandas as gpd
import requests
import zipfile
import io
from io import StringIO
import matplotlib.pyplot as plt

#pulling csv file from EPA website
url_SEDS = 'https://www.eia.gov/state/seds/CDF/Complete_SEDS.csv'
response = requests.get(url_SEDS)
csv_content = response.text

#importing data from csv file
data = StringIO(csv_content)

#bringing SEDS csv data into a pandas dataframe
raw_seds = pd.read_csv(data)

#printing the headers and first few entries for
#SEDS data to check that data was imported properly
print(raw_seds.head())

#extracting only the data for 2022 from the full SEDS dataset
seds_2022 = raw_seds[raw_seds['Year'] == 2022]

#pivoting the dataframe for SEDS 2022 data so that each category in the MSN field
#is its own column
pivot_seds2022 = seds_2022.pivot(
    index = "StateCode",
    columns = "MSN",
    values = "Data"
)

pivot_seds2022.index.name = 'STUSPS' #renaming StateCode to STUSPS to match shapefile left-join table

print(pivot_seds2022.head())

#export SEDS 2022 dataset to csv
pivot_seds2022.to_csv('/home/charley/Documents/decarbonizeSoutheast/csv/seds2022.csv')

#importing US state shapefiles from Census website
url_shape = 'https://www2.census.gov/geo/tiger/TIGER_RD18/LAYER/STATE/tl_rd22_us_state.zip'
response = requests.get(url_shapes)
with zipfile.ZipFile(io.BytesIO(response.content)) as z:
    z.extractall('/home/charley/Documents/decarbonizeSoutheast/shapes')

#importing shapefile of states from extracted directory
states_2022 = gpd.read_file('/home/charley/Documents/decarbonizeSoutheast/shapes/tl_rd22_us_state.shp')

#print the coordinate system for states_2022
print(states_2022.crs)
#print the header and first few entries in states_2022
print(states_2022.head())

#merge 2022 SEDS dataset with shapefiles
seds_states2022 = states_2022.merge(pivot_seds2022, on = 'STUSPS')

print(seds_states2022.head())

#export merged shapefile
seds_states2022.to_file('/home/charley/decarbonizeSoutheast/shapes/seds_states2022.shp')

#creating a dictionary of dataframes by year
years = raw_seds['Year'].unique()

yearly_dfs = {}

for year in years:
    seds_year = raw_seds[raw_seds['Year'] == year]
    pivot_seds_year = seds_year.pivot(
        index = "StateCode",
        columns = "MSN",
        values = "Data"
    )
    pivot_seds_year.index.name = 'STUSPS'

    yearly_dfs[year] = pivot_seds_year

    print(f"Data for Year {year}:/n", pivot_seds_year,"/n")

#join yearly datasets to state shapefiles to create a dictionary of
#shapefiles with a year of SEDS data attached to each
seds_stateshapes = {}

for year, pivot_df in yearly_dfs.items():
    seds_joinshapes = states_2022.join(pivot_df, on = 'STUSPS', how = 'left')
    seds_stateshapes[year] = seds_joinshapes

#compiling all seds_stateshapes into a GeoPackage for use in GIS applications
gpk_path = '/home/charley/Documents/decarbonizeSoutheast/shapes/seds_states.gpkg'

for year, gdf in seds_stateshapes.items():
    layer_name = f'SEDS_States{year}'
    gdf.to_file(gpk_path, layer = layer_name, driver='GPKG')

#creating a series of maps for the value of NGEIB per state per year
for year, gdf in seds_stateshapes.items():
    if 'NGEIB' not in gdf.columns:
        print(f"'NGEIB' not found for year {year}. Skipping")
        continue

    fig, ax = plt.subplots(1, 1, figsize = (10, 6))

    gdf.plot(
        column = 'NGEIB',
        cmap = 'YlOrRd',
        legend = True,
        ax = ax,
        legend_kwds = {
            'label': "Natural Gas Energy Consumed",
            'orientation': 'horizontal'
        }
    )

    ax.set_xlim([-130, -65])
    ax.set_ylim([24, 50])

    ax.set_title(f'NGEIB for {year}', fontdict = {'fontsize': 15})

    ax.set_axis_off()

    plt.savefig(f'/home/charley/Documents/decarbonizeSoutheast/figures/maps/NGEIB/ngeib_map_{year}.png', bbox_inches = 'tight')

    plt.clf()