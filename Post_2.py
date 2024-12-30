#importing libraries
import pandas as pd
import geopandas as gpd
import requests
import zipfile
import io
from io import StringIO
import os

#pulling csv file from EPA website
url_SEDS = 'https://www.eia.gov/state/seds/CDF/Complete_SEDS.csv'
response = requests.get(url_SEDS)
csv_content = response.text
data = StringIO(csv_content)
raw_seds = pd.read_csv(data)
print(raw_seds.head())

#selecting states and MSN codes to use
raw_continental_energy = raw_seds[
    (~raw_seds['StateCode'].isin(['HI', 'AK', 'X3', 'X5'])) &
    (raw_seds['MSN'].isin(['CLEIB', 'DFEIB', 'NGEIB', 'SOEGP', 'NUETP', 'HYTCP', 'GEEGP', 'WYEGP', 'TPOPP']))
]

#renaming StateCode column to match the state code column in the shapefile
raw_continental_energy.rename(columns = {'StateCode': 'STUSPS'}, inplace = True)

#pivoting table so MSN codes are the columns
continental_energy = raw_continental_energy.pivot(
    index = ['STUSPS', 'Year'],
    columns = 'MSN',
    values = 'Data'
)

#calculating statistics from SEDS datasets for energy consumption and 
def calculate_energy_metrics(df):

    #renaming StateCode column to match the state code column in the shapefile
    df.rename(columns = {'StateCode': 'STUSPS'}, inplace = True)

    #pivoting table so MSN codes are the columns
    df= df.pivot(
        index = ['STUSPS', 'Year'],
        columns = 'MSN',
        values = 'Data'
        )

    #calculate new columns based on energy emission data
    df['total_pop'] = df['TPOPP'] * 1000 #gives approximate total population for per capita calculations
    df['fossilfueldtotal'] = df['CLEIB'] + df['DFEIB'] + df['NGEIB']
    df['fossil_mWh_total'] = (df['fossilfueldtotal'] / 3412.14) * 1000 #calculating total mWh from fossil fuel sources
    df['fossil_mWh_percap'] = df['fossil_mWh_total'] / df['total_pop'] #calculating per capita mWh from fossil fuel sources
    df['coal_emiss'] = df['CLEIB'] * 95.81 #calculating CO2 equivalent of coal emissions from power plants
    df['diesel_emiss'] = df['DFEIB'] * 74.14 #calculating CO2 equivalent of diesel emissions from power plants
    df['nat_gas_emiss'] = df['NGEIB'] * 52.91 #calculating CO2 equivalent of natural gas emissions from power plants
    df['total_emissions'] = df['coal_emiss'] + df['diesel_emiss'] + df['natgas_emiss'] #calculating CO2 equivalent from all fossil fuel emissions from power plants
    df['coal_emiss_percap'] = df['CLEIB'] / df['total_pop']
    df['diesel_emiss_percap'] = df['DFEIB'] / df['total_pop']
    df['natgas_emiss_percap'] = df['NGEIB'] / df['total_pop']
    df['total_emiss_percap'] = df['coal_emiss_percap'] + df['diesel_emiss_percap'] + df['natgas_emiss_percap']

    #mWh calculations for different energy sources
    df['coal_mWh_total'] = (df['CLEIB'] / 3412.14) * 1000
    df['diesel_mWh_total'] = (df['DFEIB'] / 3412.14) * 1000
    df['natgas_mWh_total'] = (df['NGEIB'] / 3412.14) * 1000
    df['solar_mWh_total'] = (df['SOEGB'] / 3412/14) * 1000
    df['nuclear_mWh_total'] = (df['NUETB'] / 3412.14) * 1000
    df['hydro_mWh_total'] = (df['HYTCB'] / 3412.14) * 1000
    df['geo_mWh_total'] = (df['GEEGB'] / 3412.14) * 1000
    df['wind_mWh_total'] = (df['WYEGB'] / 3412.14) * 1000
    df['total_mWh_total'] = ((df['CLEIB'] + df['DFEIB'] + df['NGEIB'] + df['SOEGB'] + df['NUETB'] +
                              df['HYTCB'] + df['GEEGB'] + df['WYEGB']) / 3412.14) * 1000
    
    # mWh per capita calculations
    df['coal_mWh_percap'] = df['coal_mWh_total'] / df['total_pop']
    df['diesel_mWh_percap'] = df['diesel_mWh_total'] / df['total_pop']
    df['natgas_mWh_percap'] = df['natgas_mWh_total'] / df['total_pop']
    df['solar_mWh_percap'] = df['solar_mWh_total'] / df['total_pop']
    df['nuclear_mWh_percap'] = df['nuclear_mWh_total'] / df['total_pop']
    df['hydro_mWh_percap'] = df['hydro_mWh_total'] / df['total_pop']
    df['geo_mWh_percap'] = df['geo_mWh_total'] / df['total_pop']
    df['wind_mWh_percap'] = df['wind_mWh_total'] / df['total_pop']
    df['total_mWh_percap'] = df['total_mWh_total'] / df['total_pop']

    # Select the desired columns to return in the new DataFrame
    selected_columns = ['total_pop', 'fossilfueltotal', 'fossil_mWh_total', 'fossil_mWh_percap', 
                        'coal_emiss', 'diesel_emiss', 'natgas_emiss', 'total_emissions', 
                        'coal_emiss_percap', 'diesel_emiss_percap', 'natgas_emiss_percap', 
                        'coal_mWh_total', 'diesel_mWh_total', 'natgas_mWh_total', 
                        'solar_mWh_total', 'nuclear_mWh_total', 'hydro_mWh_total', 
                        'geo_mWh_total', 'wind_mWh_total', 'solar_mWh_percap', 
                        'nuclear_mWh_percap', 'hydro_mWh_percap', 'geo_mWh_percap', 
                        'wind_mWh_percap']

    return df[selected_columns]

continental_energy = calculate_energy_metrics(continental_energy)

#exporting pivoted table to csv
continental_energy.to_csv('/home/charley/Documents/decarbonizeSoutheast/csv/continental_energy.csv')

#importing state shapefiles
states_2022 = gpd.read_file('/home/charley/Documents/decarbonizeSoutheast/shapes/State Shapefile/tl_rd22_us_state.shp')

#merging with shapefile
continental_energy_shapes = states_2022.merge(continental_energy, on = 'STUSPS')

#making a dictionary of energy data per year to connect to the state shapefiles
years_energy = continental_energy['Year'].unique()

yearly_energy_dfs = {}

for year in years_energy:
    energy_year = raw_continental_energy[raw_continental_energy['Year'] == year]
    pivot_energy_year = energy_year.pivot(
        index = 'STUSPS',
        columns = 'MSN',
        values = 'Data'
    )
    pivot_energy_year.index.name = 'STUSPS'

    yearly_energy_dfs[year] = pivot_energy_year

    print(f'Data for Year {year}:/n', pivot_energy_year, '/n')

#joining each year dataframe to the state shapefile
energy_stateshapes = {}

for year, pivot_df in yearly_energy_dfs.items():
    energy_joinshapes = states_2022.join(pivot_df, on = 'STUSPS', how = 'left')
    energy_stateshapes[year] = energy_joinshapes

#compiling all energy df shapes into a GeoPackage for use in GIS applications
gpk_path = '/home/charley/Documents/decarbonizeSoutheast/shapes/energy_states.gpkg'

for year, gdf in energy_stateshapes.items():
    layer_name = f'State_Energy_Shapes{year}'
    gdf.to_file(gpk_path, layer = layer_name, driver = 'GPKG')

ga_energy = continental_energy.loc['GA']

print(ga_energy.head())

#method to automate exporting the energy data per state
def export_state_energy_data(state_codes, energy_data_df, output_dir = 'output'):

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    state_data = {}

    for state_code in state_codes:
        state_energy = energy_data_df.loc[state_code]

        if 'Year' in state_energy.index.names:
            state_energy = state_energy.reset_index()

        state_data[state_code] = state_energy

        csv_filename = f'{state_code}_energy_data.csv'
        csv_path = os.path.join(output_dir, csv_filename)
        state_energy.to_csv(csv_path, index = False)

        print(f'Exported: {csv_filename}')

    return state_data

#defining the output directory for csv files
csv_output = '/home/charley/Documents/decarbonizeSoutheast/csv/'

#defining sample state dataset
sample_state_energy = ['GA', 'FL', 'PA', 'WA']

sample_state_energy_data = export_state_energy_data(sample_state_energy, continental_energy, csv_output)

#defining southeastern state dataset
southeast_states = ['GA', 'FL', 'TN', 'NC', 'SC', 'AL', 'MS']

southeast_state_energy_data = export_state_energy_data(southeast_states, continental_energy, csv_output)

#calculating the sum of Georgia's carbon emissions
ga_energy_data = southeast_state_energy_data['GA']

ga_total_emissions = ga_energy_data['total_emissions'].sum()

print(ga_total_emissions)