# List columns that are the same for all turbines at a given time
# (except 'turbine' and 'Power')
non_turbine_cols = [col for col in sim_res_df.columns if col not in ['turbine', 'Power']]

# Group by datetime and aggregate
result = (
    sim_res_df
    .groupby(non_turbine_cols, as_index=False)
    .agg({'Power': 'sum'})
)

# If you want to group only by 'datetime' and keep the first value of other columns:
result = (
    sim_res_df
    .groupby('datetime', as_index=False)
    .agg({
        'Power': 'sum',
        'price': 'first',
        'PV_CF': 'first',
        'time': 'first',
        'CT': 'first',
        'h': 'first',
        'x': 'first',
        'y': 'first',
        'WD': 'first',
        'TI': 'first',
        'wd_bin_size': 'first',
        'WS': 'first',
        'P': 'first',
        'datetime': 'first'
        
        # add other columns as needed
    })
)
