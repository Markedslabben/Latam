 oks so now i want to use the latam_hybrid tools for the following:  I have the '/mnt/c/Users/klaus/klauspython/Latam/latam_hybrid/Inputdata/vortex.serie.850535.6m 164m UTC-04.0 ERA5.txt' wind   

    data at 164m height in Dominican Rep with turbine locations '/mnt/c/Users/klaus/klauspython/Latam/latam_hybrid/Inputdata/Turbine_layout_13.csv' in UTM 19N zone.
    I want to compare power curves from Vestas to see the most suitable turbine for the wind conditsion.  Now, we dont have physical measurements, bud we have virtual measuements hourly
  resolution
    11 years data 2014 - 2024 from FDC Vortex (see previous link to ERA5).

1 Wind speed data.  
First i want to show the binned wind speed data (for all years inthe time series), estimate and make a weibull fit iwth A,k parameter and also the mean wind speed, for which there is a formulat of relationship vmean as function of A,k and gamma function.  It may be a bad fit (observe histogram vs weibull plot)
Secondly i want to point out that we are useing virtual data with hourly resolution (based on ERA5 from Vortex), so real physical measurements with 10-min resolution should have more variation.  Make a quantitative assesment of the importance of this (use Ref if convenient).  als ouse the /docs folder with IEC standards etc  
Third we will use sector management due to the close distance between turbines, so as a last variation, we should also consider the effect on the production estimates when only considering the producing sectors (see previous resulta and documents).  But first i want a pure comparison of the following turbines 
Nordxex N164.csv , V162_62.csv and V163_4.5.csv 
The results should be as follows
figure 1 A plot showing histogram of wind speeds, and weibull distribution (fitted to the wind data), and all three power curves, where Nordex is at 164m HH, and the vestas turbines are at 125 and 145 m (i.e 4 combinations of tvestas turbines and heights).  We do have measurements for 164m, and use the shear (see sehar_estimate.md) to interpolate to the desired height the wind data for the power curve calculations. 
Table 1 The resulting Annual energy calculations should for the 5 cases show AEP [GWh/yr], Full load hours [hr/yr] CF [%] and Normalised AEP relative to the Nordex N164, so that normalised production for N163 is 1.  Alle the calculatesion here are based on the time series data, not weibull fit to avoid sources of error.  
Table 2 then we make a similar calculation, but now we use the weibull fit for the AEP calculation for the power curves.  Pywake can both use weibull and time series calculation for this case.  
Finally we repeat calculations in Table 1 but only for the wind speed time series whose sectors are allowed when considering sector management (see previous results documents)
All the scripts and resulting outpt shoudl be stored under /PowerCurve_analysis.  
Summarise in a report using /nivåmetoden and write to PowerCurve_analysis/power_curve_analysis.md and corresponding figures in same folder.  Make reference to the placement of the figures in the .md files Refer to sstandards and documents when required (reference list at the end).  the report should follow /nivåmetoden (i.e agent)