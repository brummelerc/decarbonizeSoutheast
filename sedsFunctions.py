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
                        'geo_mWh_total', 'wind_mWh_total', 'coal_mWh_percap',
                        'diesel_mWh_percap', 'natgas_mWh_percap', 'solar_mWh_percap', 
                        'nuclear_mWh_percap', 'hydro_mWh_percap', 'geo_mWh_percap', 
                        'wind_mWh_percap']

    return df[selected_columns]

#stacked bar chart function for energy sources
def create_stacked_bar_energy(state: str, years: list, df, filename: str):

   #filter the dataframe based on the state and years
    filtered_df = df.loc[(state, slice(None)), :].loc[(slice(None), years), :]

    if filtered_df.empty:
        print(f"No data found for {state} in the selected years: {years}")
        return
    
    #reset the index for STUSPS and Year so it can be used with plotly
    filtered_df = filtered_df.reset_index()

    #create stacked bar chart
    fig = px.bar(
        filtered_df,
        x = 'Year',
        y = ['coal_mWh_total', 'diesel_mWh_total', 'natgas_mWh_total', 
            'solar_mWh_total', 'nuclear_mWh_total', 'hydro_mWh_total', 
            'geo_mWh_total', 'wind_mWh_total'],
        title = f'Energy Sources in {state} for Selected Years',
        labels = {'value': 'Energy Produced (mWh)', 'variable': 'Energy Source'},
        color_discrete_sequence = px.colors.qualitative.Pastel
        )
    
    #export the bar chart as a figure
    fig.write_image(filename)
    print(f'Chart Exported as {filename}')

#stacked bar chart function for energy sources per capita
def create_stacked_bar_energy_percap(state: str, years: list, df, filename: str):

    #filter the dataframe based on the state and years
    filtered_df = df.loc[(state, slice(None)), :].loc[(slice(None), years), :]

    if filtered_df.empty:
        print(f"No data found for {state} in the selected years: {years}")
        return
    
    #reset the index for STUSPS and Year so it can be used in plotly
    filtered_df = filtered_df.reset_index()

    #create stacked bar chart
    fig = px.bar(
        filtered_df,
        x = 'Year',
        y = ['coal_mWh_percap', 'diesel_mWh_percap', 'natgas_mWh_percap', 
             'solar_mWh_percap', 'nuclear_mWh_percap', 'hydro_mWh_percap', 
             'geo_mWh_percap', 'wind_mWh_percap'],
        title = f'Energy Sources Per Capita in {state} for Selected Years',
        labels = {'value': 'Energy Produced (mWh) per capita', 'variable': 'Energy Source'},
        color_discrete_sequence = px.colors.qualitative.Pastel
        )
    
    #export the bar chart as a figure
    fig.write_image(filename)
    print(f'Chart Exported as {filename}')

#stacked bar chart function for emissions 
def create_stacked_bar_emissions(state: str, years: list, df, filename: str):

    #filter the dataframe based on the state and years
    filtered_df = df.loc[(state, slice(None)), :].loc[(slice(None), years), :]

    if filtered_df.empty:
        print(f"No data found for {state} in the selected years: {years}")
        return
    
    #reset the index for STUSPS and Year so it can be used in plotly
    filtered_df = filtered_df.reset_index()

    #create stacked bar chart
    fig = px.bar(
        filtered_df,
        x = 'Year',
        y = ['coal_emiss', 'diesel_emiss', 'natgas_emiss'],
        title = f'CO2 Emissions in {state} for Selected Years',
        labels = {'value': 'CO2 Equivalent Emissions', 'variable': 'Energy Source'},
        color_discrete_sequence = px.colors.qualitative.Pastel
        )
    
    #export the bar chart as a figure
    fig.write_image(filename)
    print(f'Chart Exported as {filename}')

#stacked bar chart for emissions per capita
def create_stacked_bar_emissions_percap(state: str, years: list, df, filename: str):

    #filter the dataframe based on the state and years
    filtered_df = df.loc[(state, slice(None)), :].loc[(slice(None), years), :]

    if filtered_df.empty:
        print(f"No data found for {state} in the selected years: {years}")
        return
    
    #reset the index for STUSPS and Year so it can be used with plotly
    filtered_df = filtered_df.reset_index()

    #create stacked bar chart
    fig = px.bar(
        filtered_df,
        x = 'Year',
        y = ['coal_emiss_percap', 'diesel_emiss_percap', 'natgas_emiss_percap'],
        title = f'CO2 Emissions Per Capita in {state} for Selected Years',
        labels = {'value': 'CO2 Equivalant Emissions per capita', 'variable': 'Energy Source'},
        color_discrete_sequence = px.colors.qualitative.Pastel
        )
    
    #export the bar chart as a figure
    fig.write_image(filename)
    print(f'Chart Exported as {filename}')