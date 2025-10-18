"""
Working Wind Energy Analysis Example

This example uses only the components that work in your environment:
- AnalysisConfig
- WindEnergyPipeline

The solar components have DLL loading issues, but wind analysis works fine.
"""

# Import only the working components
from energy_analysis import AnalysisConfig, WindEnergyPipeline
import pandas as pd
import matplotlib.pyplot as plt

def main():
    print("=== Wind Energy Analysis Example ===")
    print()
    
    # Create configuration
    config = AnalysisConfig()
    
    # Show current configuration
    print("Current Configuration:")
    print(f"Site coordinates: {config.site.latitude}, {config.site.longitude}")
    print(f"Wind data file: {config.wind.vortex_data_path}")
    print(f"Turbine model: {config.wind.turbine_name}")
    print(f"Wake model: {config.wind.wake_model}")
    print(f"Layout file: {config.wind.layout_csv_path}")
    print()
    
    # Create wind pipeline with separate wind and site configs
    wind_pipeline = WindEnergyPipeline(config.wind, config.site)
    
    # Check what files are available
    import os
    print("Checking required files:")
    files_to_check = [
        config.wind.vortex_data_path,
        config.wind.layout_csv_path,
        config.wind.turbine_csv_path
    ]
    
    all_files_exist = True
    for file_path in files_to_check:
        exists = os.path.exists(file_path)
        status = "✅" if exists else "❌"
        print(f"{status} {file_path}")
        if not exists:
            all_files_exist = False
    
    print()
    
    if all_files_exist:
        print("All files found! Running wind analysis...")
        try:
            # Run the complete wind analysis pipeline
            results = (wind_pipeline
                      .load_turbine()
                      .create_site()
                      .load_layout()
                      .setup_wind_farm_model()
                      .run_simulation()
                      .process_results())
            
            print("✅ Wind analysis completed successfully!")
            print(f"Results type: {type(results)}")
            
            # Show some basic results if available
            if hasattr(wind_pipeline, 'simulation_result'):
                sim_result = wind_pipeline.simulation_result
                print(f"Simulation result type: {type(sim_result)}")
                
                # Try to get basic statistics
                try:
                    aep = sim_result.aep()
                    print(f"Annual Energy Production: {aep}")
                except Exception as e:
                    print(f"Could not get AEP: {e}")
            
        except Exception as e:
            print(f"❌ Error during wind analysis: {e}")
            print("This might be due to missing data files or configuration issues.")
    
    else:
        print("❌ Some required files are missing.")
        print("Please check that you have:")
        print("- Vortex wind data file")
        print("- Layout coordinates file") 
        print("- Turbine specification files")
        print()
        print("You can still test the pipeline setup:")
        
        try:
            # Test just the turbine loading
            wind_pipeline.load_turbine()
            print("✅ Turbine loading works")
        except Exception as e:
            print(f"❌ Turbine loading failed: {e}")

if __name__ == "__main__":
    main() 