#!/usr/bin/env python3
"""
Example: New Hybrid Energy Analysis Workflow

This script demonstrates the new object-oriented approach to energy analysis.
Compare this with your old scripts to see the improvements!
"""

from energy_analysis import HybridEnergyAnalysis, AnalysisConfig

def main():
    print("="*60)
    print("HYBRID ENERGY ANALYSIS - NEW WORKFLOW")
    print("="*60)
    
    # Method 1: Quick analysis with defaults
    print("\n1. Quick Analysis with Defaults:")
    print("-" * 40)
    
    try:
        # One-liner for complete analysis
        analysis = HybridEnergyAnalysis.from_defaults()
        
        # Validate setup
        validation = analysis.validate_setup()
        if not validation['valid']:
            print("❌ Missing required files:")
            for file in validation['missing_files']:
                print(f"   - {file}")
            print("\nPlease ensure all input files are available before running analysis.")
            return
        
        print("✅ All required files found!")
        
        # Run complete analysis
        print("\nRunning full hybrid analysis...")
        analysis.run_full_analysis()
        
        # Print summary
        analysis.print_summary()
        
        # Export results
        exported_files = analysis.export_results()
        print(f"\n📁 Results exported to {len(exported_files)} files:")
        for result_type, file_path in exported_files.items():
            print(f"   - {result_type}: {file_path}")
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        print("\nThis is likely due to missing input files.")
        print("The new system will show you exactly what's missing!")
    
    # Method 2: Custom configuration
    print("\n\n2. Custom Configuration Example:")
    print("-" * 40)
    
    # Create custom config
    config = AnalysisConfig()
    config.wind.start_year = 2020
    config.wind.end_year = 2022
    config.wind.wake_model = "BastankhahGaussianDeficit"  # Enable wake effects
    config.solar.installed_capacity_MW = 200.0  # Increase solar capacity
    
    print("Custom configuration created:")
    print(f"  - Analysis period: {config.wind.start_year}-{config.wind.end_year}")
    print(f"  - Wake model: {config.wind.wake_model}")
    print(f"  - Solar capacity: {config.solar.installed_capacity_MW} MW")
    
    # Method 3: Step-by-step with method chaining
    print("\n\n3. Method Chaining Example:")
    print("-" * 40)
    
    try:
        step_analysis = HybridEnergyAnalysis.from_defaults()
        
        # Wind analysis with method chaining
        print("Running wind analysis with method chaining...")
        wind_results = (step_analysis.wind
                       .load_turbine()
                       .create_site()
                       .load_layout()
                       .setup_wind_farm_model("NoWakeDeficit")
                       .run_simulation()
                       .process_results())
        
        print(f"✅ Wind analysis complete!")
        print(f"   Annual energy: {wind_results.results['annual_energy_GWh']:.2f} GWh")
        
        # Solar analysis with method chaining
        print("\nRunning solar analysis with method chaining...")
        solar_results = (step_analysis.solar
                        .load_pvgis_data()
                        .process_results())
        
        print(f"✅ Solar analysis complete!")
        print(f"   Annual energy: {solar_results.results['annual_energy_MWh']:.2f} MWh")
        
    except Exception as e:
        print(f"❌ Step-by-step analysis failed: {e}")
    
    print("\n\n4. Key Advantages of New System:")
    print("-" * 40)
    print("✅ No more importlib.reload() needed!")
    print("✅ Method chaining for clean workflows")
    print("✅ Automatic data flow between steps")
    print("✅ Centralized configuration management")
    print("✅ Better error messages and validation")
    print("✅ Structured result organization")
    print("✅ Easy export and reporting")
    print("✅ Jupyter notebook friendly")
    
    print("\n\n5. Comparison with Old Workflow:")
    print("-" * 40)
    print("OLD WAY:")
    print("  import importlib")
    print("  importlib.reload(turbine_galvian.create_turbine)")
    print("  importlib.reload(site_galvian.create_site)")
    print("  turbine = create_nordex_n164_turbine('Inputdata/Nordex N164.csv')")
    print("  site = create_site_from_vortex('Inputdata/vortex...', start='2014-01-01')")
    print("  # ... many manual steps ...")
    print("")
    print("NEW WAY:")
    print("  analysis = HybridEnergyAnalysis.from_defaults()")
    print("  analysis.run_full_analysis()")
    print("  analysis.print_summary()")
    print("")
    print("OR with method chaining:")
    print("  results = (analysis.wind")
    print("            .load_turbine()")
    print("            .create_site()")
    print("            .run_simulation())")

if __name__ == "__main__":
    main() 