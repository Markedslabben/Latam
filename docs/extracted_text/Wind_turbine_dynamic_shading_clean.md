# Wind Turbine Dynamic Shading: The Effects on Combined Solar and Wind Farms

*Published in Journal of Renewable and Sustainable Energy 15, 063703 (2023)*  
*DOI: 10.1063/5.0176121*

## Authors
- Nico J. Dekker¹
- Lenneke H. Slooff¹
- Mark J. Jansen¹
- Gertjan de Graaff¹
- Jaco Hovius²
- Rudi Jonkman³
- Jesper Zuurbier⁴
- Jan Pronk⁵

### Affiliations
1. TNO Solar Energy, Westerduinweg 3, 1755 LE Petten, The Netherlands
2. Vattenfall, Hoekenrode 8, 1102BR Amsterdam, The Netherlands
3. Heliox, De Waal 24, 5684PH Best, The Netherlands
4. Uw-Stroom, Warmenhuizen, The Netherlands
5. Prosoldiga, Schagen, The Netherlands

*Corresponding authors:*  
- nico.dekker@tno.nl
- lenneke.slooff@tno.nl

## Abstract

The Dutch climate agreement anticipates the large-scale implementation of solar and wind energy systems on land and water. Combining solar and wind farms has the benefit of multiple surface area use, and it also has the advantage of energy generation from both solar and wind energy systems, which is rather complementary in time; thus, a better balance can be found between electricity generation and demand and the load on the electricity grid. 

In combined solar and wind farms (CSWFs), the turbines will cast shadows on the solar panels. This concerns the static shadow from the construction tower of the turbine as well as the dynamic shadow caused by the rotating blades. This paper reports on the results of millisecond data monitoring of the PV farm of a CSWF in the Netherlands on land. Static and dynamic shadow effects are discussed, as well as their dependency on farm design. 

It is observed that the dynamic shade of the wind turbine blade causes serious disturbances of the DC inputs of the inverter, resulting in deviation of the maximum power point tracking monitored. The shadow of the wind turbine results in a total energy loss of about 6% for the given period, park configuration, PV modules, inverter type, and setting.

## I. Introduction

In the different energy scenarios, a large role is foreseen for deployment of large-scale solar and wind energy on land and water. Morris et al.'s prediction for 2050 is wind and solar contribution of about 10,000 EJ in the global electricity production of total 41,000 EJ, meaning roughly 24%. The contribution in the Global Primary Energy supply is about half of that. DNV has a higher estimate with a share of 11% for wind and 17% for solar, in the world primary energy supply.

However, grid congestion problems drastically slow down the implementation in several countries. Some short-term solutions include:

1. **Curtailment**: Limiting the electricity generation from solar and wind farms to stay below the rated grid capacity.

2. **Cable Pooling**: Using a single connection cable for more than one power plant, e.g., a solar and wind farm.

### Benefits of Combined Solar and Wind Farms (CSWFs):

- **For Power Consumers:**
  - Lower costs for renewable energy generation
  - Lower grid costs

- **For CSWF Developers:**
  - No additional grid connection waiting time and costs
  - Lower costs for land

- **For Grid Operators:**
  - More constant grid load
  - Less grid reinforcement needed

### Technical Challenges

The proximity of wind turbines introduces two types of shading on PV systems:
1. Static shade from the turbine tower
2. Dynamic shade from the moving rotor blades (frequency range: 0.25-1.2 Hz)

## II. PV Plant and Monitoring System

### Study Period
August 14, 2022 - February 2, 2023

### PV Plant Specifications
- 115,232 Solar Panels (Total 38 MWdc)
- 163 String Inverters (Total 30 MWAC)
- 32 panels per string in series (60 full-cell solar panels, 325-330 Wp each)
- Panels mounted in portrait orientation, two rows
- Wind turbine tip height: 150m

### Monitoring System
Two monitoring purposes:
1. **DC and AC Yield Effects:**
   - DC voltage, current, power, and energy monitoring
   - Three-phase AC measurements
   - In-plane irradiance and temperature monitoring
   - 6-second logging interval

2. **MPPT and Dynamic Response:**
   - Millisecond-level monitoring of voltage and current
   - Module voltage monitoring at string start, middle, and end
   - High-precision irradiance measurements 

## III. Results and Analysis

### A. DC Yield Effects

The DC yield of the monitored strings shows significant variations between shaded and unshaded conditions. On September 1st, 2022, clear differences were observed:

1. **Reference System (Unshaded):**
   - Normal operation with expected voltage and current profiles
   - Only minor disturbances from cloud cover between 13:00-14:00 CET
   - Temperature-dependent voltage variations (approximately 33°C higher at noon)

2. **Shaded System:**
   - Tower shadow impact observed before 10:00 CET
   - Blade shadow effects causing periodic power reductions
   - Complex MPPT behavior under dynamic shading

### B. Irradiance and System Response

The monitoring system captured several key phenomena:

1. **Irradiance Patterns:**
   - Tower shadow causing sharp drops in irradiance
   - Cloud effects between 13:00-14:00 CET showing both reduction and enhancement
   - Clear distinction between static (tower) and dynamic (blade) shading

2. **Voltage and Current Behavior:**
   - Unshaded reference system showing expected responses to irradiance changes
   - Temperature correction applied using coefficients:
     - Impp temperature coefficient: 0.048°C
     - Vmpp temperature coefficient: -0.42°C/°C
     - Pmpp temperature coefficient: -0.37°C

### C. Dynamic Shading Analysis

Four distinct MPPT deviation patterns were identified:

1. **Voltage Increase from Vmpp to 1150V:**
   - Regular blade shading every 2.5 seconds
   - Irradiance drops from 600 W/m² to 100-200 W/m²
   - Blade shadow traversal time: 0.3 seconds
   - String shading duty cycle: 12% shaded, 88% unshaded

2. **MPPT Algorithm Response:**
   - Normal conditions: 4-second nominal voltage, 2-second step adjustments
   - Shaded conditions: Increased step size (18V) with 1-second intervals
   - Voltage increase from 970V to 1150V over 50 seconds
   - Power reduction up to 50% due to excess voltage

3. **Continuous Voltage Sweep:**
   - Algorithm transition at 09:15 CET
   - Tower shadow affecting 15-20% of string voltage
   - Vmpp reduction to approximately 850V
   - Rapid voltage adjustments (3000 V/s) during blade shading

4. **Current Limitations:**
   - Maximum current: 15A (below inverter limit of 26A)
   - Current limitation by PV module specifications
   - Bypass diode activation during severe shading
   - Cell temperature impacts on performance

### D. Power Loss Analysis

The dynamic shading effects resulted in significant power losses:

1. **Direct Shading Losses:**
   - Tower shadow: 15-20% voltage reduction
   - Blade shadow: 12% time impact with 80-90% power reduction

2. **MPPT-Related Losses:**
   - Suboptimal voltage operation causing up to 50% additional losses
   - Algorithm adaptation issues under rapid shading changes
   - Bypass diode activation contributing to voltage drops

3. **Temperature Effects:**
   - Module temperature approximately 33°C above morning temperatures
   - Voltage reduction correlating with temperature increase
   - Impact on overall system efficiency

### E. System Performance Implications

The study revealed several critical findings:

1. **Overall Impact:**
   - Total energy loss approximately 6% during study period
   - Losses concentrated in morning and evening hours
   - Seasonal variations in impact severity

2. **Operational Considerations:**
   - MPPT algorithm limitations under dynamic shading
   - Inverter response time constraints
   - Module bypass behavior affecting string performance

3. **Design Recommendations:**
   - Minimum distance requirements from wind turbines
   - MPPT algorithm optimization opportunities
   - String configuration considerations for shaded conditions 

## IV. Discussion

### A. MPPT Performance Under Dynamic Shading

The study revealed significant challenges in MPPT operation under wind turbine shading:

1. **Algorithm Limitations:**
   - Standard MPPT algorithms struggle with rapid shadow transitions
   - Voltage adjustments often lag behind shading changes
   - Power optimization becomes complex under periodic shading

2. **System Response:**
   - Inverter voltage sweeps may not align with optimal power points
   - Bypass diode activation creates additional complexity
   - Temperature effects compound the challenges of dynamic shading

### B. Energy Loss Mechanisms

Multiple factors contribute to the observed 6% energy loss:

1. **Direct Shading Effects:**
   - Physical obstruction from tower and blades
   - Varying impact based on sun position and time of day
   - Seasonal variations in shading patterns

2. **Secondary Effects:**
   - MPPT algorithm inefficiencies
   - Thermal impacts on module performance
   - String mismatch losses

### C. Design Implications

The findings suggest several important considerations for CSWF design:

1. **Layout Optimization:**
   - Strategic placement of PV arrays relative to wind turbines
   - Consideration of seasonal sun paths
   - Balance between land use efficiency and shading mitigation

2. **Technical Solutions:**
   - Advanced MPPT algorithms for dynamic shading
   - Potential for module-level power optimization
   - Alternative string configurations

## V. Conclusions

The comprehensive analysis of wind turbine shading effects on solar PV performance in a combined solar and wind farm has revealed several key findings:

1. **Shading Impact:**
   - Total energy loss of approximately 6% during the study period
   - Dynamic blade shading causing complex system responses
   - Static tower shading creating predictable power reductions

2. **Technical Challenges:**
   - MPPT algorithms require optimization for dynamic shading
   - System response limitations under rapid shadow transitions
   - Temperature effects influencing overall performance

3. **Design Recommendations:**
   - Implement minimum spacing requirements between turbines and PV arrays
   - Consider advanced power optimization technologies
   - Optimize string configurations for shaded conditions

4. **Future Considerations:**
   - Development of specialized MPPT algorithms
   - Integration of smart monitoring systems
   - Balance between land use efficiency and system performance

The study demonstrates that while combined solar and wind farms offer significant advantages in land use and grid integration, careful consideration must be given to the technical challenges of wind turbine shading effects on PV performance. Future developments in inverter technology and system design will be crucial in optimizing the performance of these hybrid energy systems.

## Acknowledgments

The authors gratefully acknowledge the support of the Dutch Ministry of Economic Affairs and Climate Policy. Special thanks to the technical staff at TNO Solar Energy and the cooperation of Vattenfall, Heliox, Uw-Stroom, and Prosoldiga in facilitating this research.

## References

[References have been omitted in this markdown version. Please refer to the original paper for complete references.] 