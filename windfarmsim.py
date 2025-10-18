# Wind farm simulation
# Uses windfarm_layout package 

# import packages
import importlib
import windfarm_layout as wfl
importlib.reload(wfl)
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt

# load data
layers = wfl.load_all_layers("inputdata/Dominikanske republikk.gpkg")
# Create figure and axis
# Create figure and axis
fig, ax = wfl.create_plot(figsize=(15,10))

# Plot all layers using plot_layers function
wfl.plot_layers(layer_dict=layers, ax=ax)
plt.show()
