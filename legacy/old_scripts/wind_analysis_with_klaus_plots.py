"""
Wind Analysis with Klaus's Existing Plotting Functions

This example demonstrates how to use the WindEnergyPipeline with Klaus's 
original plotting functions from simulation/results.py and other modules.
"""

from energy_analysis import AnalysisConfig, WindEnergyPipeline
import matplotlib.pyplot as plt

def main():
    print("🌪️ Wind Analysis with Klaus's Original Plotting Functions")
    print("=" * 60)
    
    # Setup and run analysis
    config = AnalysisConfig()
    wind = WindEnergyPipeline(config.wind, config.site)
    
    print("Running full analysis pipeline...")
    wind.run_full_pipeline()
    
    print(f"✅ Analysis complete!")
    print(f"   Annual energy: {wind.results['annual_energy_GWh']:.1f} GWh")
    print(f"   Capacity factor: {wind.results['capacity_factor']:.1%}")
    print(f"   Wake model: {wind.metadata['wake_model']}")
    print()
    
    # Now use Klaus's existing plotting functions
    print("📊 Creating plots using Klaus's existing functions...")
    print()
    
    # 1. Production profiles (yearly, seasonal, diurnal)
    print("1. Production profiles (Klaus's plot_production_profiles)...")
    try:
        yearly, monthly_avg, diurnal = wind.plot_production_profiles()
        print("   ✅ Production profiles created")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 2. Turbine production comparison
    print("2. Turbine production comparison (Klaus's plot_turbine_production)...")
    try:
        wind.plot_turbine_production()
        print("   ✅ Turbine production comparison created")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. Energy rose
    print("3. Energy rose (Klaus's plot_energy_rose)...")
    try:
        wind.plot_energy_rose()
        print("   ✅ Energy rose created")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 4. Wind direction vs mean power
    print("4. Wind direction vs mean power (Klaus's plot_wind_direction_vs_mean_power)...")
    try:
        wind.plot_wind_direction_vs_mean_power()
        print("   ✅ Wind direction vs power plot created")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 5. Weibull site distributions
    print("5. Weibull site distributions (Klaus's plot_wbl_site)...")
    try:
        wind.plot_wbl_site()
        print("   ✅ Weibull distributions plot created")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 6. Wind speed histogram
    print("6. Wind speed histogram (Klaus's plot_wind_speed_histogram)...")
    try:
        wind.plot_wind_speed_histogram()
        print("   ✅ Wind speed histogram created")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 7. Wind rose from site
    print("7. Wind rose from site (Klaus's plot_wind_rose_from_site)...")
    try:
        wind.plot_wind_rose_from_site()
        print("   ✅ Wind rose from site created")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 8. Wake maps
    print("8. Wake maps (Klaus's plot_wake_maps)...")
    try:
        # Use specific wind directions and speeds for the site
        wd_ws_list = [(60, 10), (120, 10), (240, 6), (300, 8)]
        wind.plot_wake_maps(wd_ws_list=wd_ws_list)
        print("   ✅ Wake maps created")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 9. GIS layers (if available)
    print("9. GIS layers (Klaus's plot_layers)...")
    try:
        wind.plot_layers()
        print("   ✅ GIS layers plot created")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("🎨 All plotting functions tested!")
    print()
    print("Available plotting methods from Klaus's original functions:")
    print("  - wind.plot_production_profiles()      # Yearly, seasonal, diurnal")
    print("  - wind.plot_turbine_production()       # Stacked bar comparison")
    print("  - wind.plot_energy_rose()              # Polar power plot")
    print("  - wind.plot_wind_direction_vs_mean_power()  # Histogram")
    print("  - wind.plot_wake_maps()                # Wake visualization")
    print("  - wind.plot_wbl_site()                 # Weibull distributions")
    print("  - wind.plot_wind_speed_histogram()     # Wind speed distribution")
    print("  - wind.plot_wind_rose_from_site()      # Wind rose")
    print("  - wind.plot_layers()                   # GIS layers")
    print("  - wind.plot_all_profiles()             # All profiles (if PV data available)")
    
    return wind

if __name__ == "__main__":
    wind_pipeline = main()
    
    # Keep plots open
    plt.show() 