#!/usr/bin/env python3
"""
Test script to verify the fixed issues in WindEnergyPipeline.
"""

from energy_analysis import AnalysisConfig, WindEnergyPipeline
import matplotlib.pyplot as plt

def test_capacity_factor_fix():
    """Test that capacity factor is now calculated correctly."""
    print("🔧 Testing capacity factor fix...")
    
    # Initialize pipeline
    config = AnalysisConfig()
    wind = WindEnergyPipeline(config.wind, config.site, verbose=False)
    
    # Run analysis
    wind.run_full_pipeline()
    
    # Get summary with fixed capacity factor
    summary = wind.get_summary()
    cf = summary['results_summary']['capacity_factor']
    
    print(f"   Capacity factor: {cf:.2%}")
    print(f"   Annual energy: {summary['results_summary']['annual_energy_GWh']:.1f} GWh")
    print(f"   Turbine rated power: {summary['results_summary']['turbine_rated_power_MW']:.1f} MW")
    print(f"   Total capacity: {summary['results_summary']['total_rated_capacity_MW']:.1f} MW")
    
    # Verify capacity factor is reasonable (should be < 100%)
    if 0 < cf < 1:
        print("   ✅ Capacity factor is now reasonable!")
        return True
    else:
        print(f"   ❌ Capacity factor still wrong: {cf:.2%}")
        return False

def test_plotting_functions():
    """Test that plotting functions work without errors."""
    print("\n🎨 Testing plotting functions...")
    
    # Initialize pipeline
    config = AnalysisConfig()
    wind = WindEnergyPipeline(config.wind, config.site, verbose=False)
    wind.run_full_pipeline()
    
    try:
        # Test production profiles
        print("   Testing plot_production_profiles...")
        wind.plot_production_profiles()
        plt.close('all')  # Close plots to avoid display issues
        print("   ✅ Production profiles work!")
        
        # Test energy rose
        print("   Testing plot_energy_rose...")
        wind.plot_energy_rose()
        plt.close('all')
        print("   ✅ Energy rose works!")
        
        # Test wind direction vs power
        print("   Testing plot_wind_direction_vs_mean_power...")
        wind.plot_wind_direction_vs_mean_power()
        plt.close('all')
        print("   ✅ Wind direction vs power works!")
        
        # Test wind speed histogram
        print("   Testing plot_wind_speed_histogram...")
        wind.plot_wind_speed_histogram()
        plt.close('all')
        print("   ✅ Wind speed histogram works!")
        
        # Test wind rose from site
        print("   Testing plot_wind_rose_from_site...")
        wind.plot_wind_rose_from_site()
        plt.close('all')
        print("   ✅ Wind rose from site works!")
        
        # Test wake maps (this might take longer)
        print("   Testing plot_wake_maps...")
        wind.plot_wake_maps(wd_ws_list=[(60, 10)])
        plt.close('all')
        print("   ✅ Wake maps work!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Plotting error: {e}")
        return False

def test_turbine_production_with_wake():
    """Test the turbine production plot that requires two simulations."""
    print("\n⚡ Testing turbine production plot (with/without wake)...")
    
    # Initialize pipeline
    config = AnalysisConfig()
    wind = WindEnergyPipeline(config.wind, config.site, verbose=False)
    wind.run_full_pipeline()
    
    try:
        print("   Running turbine production comparison...")
        wind.plot_turbine_production()
        plt.close('all')
        print("   ✅ Turbine production comparison works!")
        return True
        
    except Exception as e:
        print(f"   ❌ Turbine production error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Fixed Issues in WindEnergyPipeline")
    print("=" * 50)
    
    # Test capacity factor fix
    cf_ok = test_capacity_factor_fix()
    
    # Test plotting functions
    plot_ok = test_plotting_functions()
    
    # Test turbine production with wake
    turbine_ok = test_turbine_production_with_wake()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Capacity factor fix: {'✅ PASS' if cf_ok else '❌ FAIL'}")
    print(f"   Plotting functions: {'✅ PASS' if plot_ok else '❌ FAIL'}")
    print(f"   Turbine production: {'✅ PASS' if turbine_ok else '❌ FAIL'}")
    
    if all([cf_ok, plot_ok, turbine_ok]):
        print("\n🎉 All tests passed! Issues are fixed.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.") 