try:
    print("Attempting to import dependencies...")
    import numpy
    print("✓ numpy imported successfully")
    import pandas
    print("✓ pandas imported successfully")
    import fiona
    print("✓ fiona imported successfully")
    import shapely
    print("✓ shapely imported successfully")
    import pyproj
    print("✓ pyproj imported successfully")
    
    print("\nAttempting to import geopandas...")
    import geopandas
    print("✓ geopandas imported successfully")
    
    print("\nGeopandas version:", geopandas.__version__)
    print("All imports successful!")
    
except Exception as e:
    print("\nError occurred:")
    print(type(e).__name__, ":", str(e)) 