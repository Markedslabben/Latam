# TODO: Update Power Curve Analysis with Corrected Loss Calculations

**Date**: 2025-10-26
**Status**: Ready to execute in IPython
**Estimated Time**: 1.5-2 hours total (20-30 min execution + report update)

---

## Background

Two critical bugs were fixed in the loss calculation system (2025-10-26):

1. **Other Losses Bug Fixed** (`latam_hybrid/wind/site.py:441-447`)
   - BEFORE: Other losses and net production were swapped
   - Net production showed 1.5-2.2 GWh instead of ~18-20 GWh
   - AFTER: Correctly calculated - 8.8% losses, 91.2% remains

2. **Sector Management Bug Fixed** (`latam_hybrid/wind/site.py:738-839`)
   - BEFORE: Time-based calculation → 12.98% farm-level losses
   - AFTER: Energy-based calculation → 5.87% farm-level losses
   - Now accounts for wind speed/frequency variations by direction

**Impact**: All new simulations automatically use corrected calculations. Old reports need to be regenerated.

---

## Current State of Power Curve Analysis

**Existing Report**: `PowerCurve_analysis/power_curve_analysis.md`

**Existing Tables** (Tables 1-3):
- Created by `scripts/power_curve_comparison_v2.py`
- **NO wake modeling** - just power curve application
- **NO losses** - gross production only
- **NO PyWake simulation**
- Uses simple methods: time series, Weibull, sector filtering

**Problem**: Report doesn't include realistic production with:
- Wake losses from turbine interactions
- Corrected sector management losses (energy-based)
- Other losses (availability, electrical, etc.)

---

## What Needs to Be Done

### Objective

Create **NEW Table 4** with full PyWake wake modeling + corrected loss calculations for all 5 turbine configurations using the FULL 11.3-year dataset.

### Turbine Configurations to Analyze
# Note i have changed the below row order of the turbine types compared to existing implementation, because i want to cdifferences betwee Vestas 6.2 and 4.5 production output 
1. Nordex N164 @ 164m (7.0 MW)
2. Vestas V162-6.2 @ 145m (6.2 MW)
2. Vestas V163-4.5 @ 145m (4.5 MW)  
3. Vestas V162-6.2 @ 125m (6.2 MW)
4. Vestas V163-4.5 @ 125m (4.5 MW)

Each configuration uses:
- **13-turbine layout** (same layout for all)
- **Full wind dataset**: 99,000 hourly records (11.3 years)
- **PyWake simulation**: Bastankhah-Gaussian wake model
- **Sector management**: Turbines 1,3,5,7,9,12 restricted to 60-120° and 240-300°
- **Include correct losses**: Wake,  Sector (energy-based) and  Other (8.8%)

---

## Step-by-Step Execution Plan

### Step 1: Create New Analysis Script

**File**: `PowerCurve_analysis/scripts/power_curve_with_losses.py`

**Status**: NEEDS TO BE CREATED

**What it should do**:
1. Load full 11-year wind dataset (must be whole years)
2. For each turbine configuration:
   - Adjust wind speed to correct hub height (power law)
   - Load turbine power curve
   - Run PyWake simulation with:
     - Bastankhah-Gaussian wake model
     - Time series method (hourly data)
     - Apply other losses (losses.csv)
     - Sector management (energy-based, with the updated sector management model)
     - Compute losses enabled
   - Calculate final production
3. Export results to CSV tables. 
   The CSV tables should have added a column at the right end, showing the fractional difference between Vestas 6.2 and Vestas 4.5 (at the same heights), which can be done by looking at the frational production / normalised production column and just taking the difference of the two i.e Vestas 6.2   - Vestas 4.5   is 0.785 - 0.651 = 0.134
4. Generate per-turbine loss breakdowns

**Expected Runtime**: 20-30 minutes for all 5 configurations (each requires dual PyWake simulation)

### Step 2: Execute Script in IPython

**Why IPython?**: Faster execution, already configured with autoreload

**Commands**:
```bash
cd /mnt/c/Users/klaus/klauspython/Latam
ipython

# Inside IPython:
%run PowerCurve_analysis/scripts/power_curve_with_losses.py
```

**What to expect**:
- Console output showing progress for each configuration
- CSV files created in `PowerCurve_analysis/results/`
- Per-turbine loss tables for detailed analysis

### Step 3: Review Generated Results

**Output files** (will be created):
1. `PowerCurve_analysis/results/table4_pywake_with_losses.csv` - Summary table
2. `PowerCurve_analysis/results/per_turbine_losses_Nordex_N164_164m.csv`
3. `PowerCurve_analysis/results/per_turbine_losses_V162-6.2_145m.csv`
4. `PowerCurve_analysis/results/per_turbine_losses_V162-6.2_125m.csv`
5. `PowerCurve_analysis/results/per_turbine_losses_V163-4.5_145m.csv`
6. `PowerCurve_analysis/results/per_turbine_losses_V163-4.5_125m.csv`

**Validation checks**:
- ✅ Sector losses should be ~5-6% farm-level (NOT 12-13%)
- ✅ Other losses should be ~8.8% (NOT 91.2%)
- ✅ Wake losses should be ~9-11% (varies by configuration)
- ✅ Loss cascade should sum correctly: gross - wake - sector - other ≈ net

### Step 4: Update Report Markdown

**File to modify**: `PowerCurve_analysis/power_curve_analysis.md`

**Changes needed**:

1. **Add new section 1.2.4**: "PyWake Simulation with Full Loss Modeling (Table 4)"
   - Location: After section 1.2.3 (around line 150)
   - Content:
     - Description of PyWake simulation approach
     - Wake model: Bastankhah-Gaussian
     - Sector management: Energy-based losses (corrected)
     - Other losses: Availability, electrical, environmental (8.8% total)
     - Results interpretation

2. **Add Table 4**: Full results table with columns:
   - Configuration
   - Gross AEP (GWh/yr) - before losses
   - Wake Loss (%)
   - Sector Loss (%)
   - Other Losses (%)
   - Net AEP (GWh/yr) - final realistic production
   - Capacity Factor (%)
   - Full Load Hours (hr/yr)

3. **Update Executive Summary** (Hovedbudskap):
   - Include realistic net production with all losses
   - Update capacity factors
   - Revise recommendations based on net production

4. **Add loss breakdown discussion**:
   - Compare gross (Table 1) vs net (Table 4) production
   - Explain ~25-30% total losses (wake + sector + other)
   - Highlight importance of wake modeling for farm design

5. **Add reference to detailed loss methodology**:
   - Link to `latam_hybrid/claudedocs/loss_calculation_methodology.md`
   - Explain dual simulation approach
   - Document energy-based sector loss calculation

### Step 5: Generate Word Document (Optional)

**If needed for stakeholders**:

```bash
cd /mnt/c/Users/klaus/klauspython/Latam
python PowerCurve_analysis/scripts/md_to_docx.py
```

**Output**: `PowerCurve_analysis/power_curve_analysis.docx`

---

## Expected Results (Table 4 Preview)

**Estimated values** (actual results from simulation may vary):

| Configuration | Gross AEP | Wake Loss | Sector Loss | Other Loss | Net AEP | CF | FLH |
|---|---|---|---|---|---|---|---|
| Nordex N164 @ 164m | ~280 GWh | ~10.2% | ~5.9% | ~8.8% | ~234 GWh | ~29.4% | 2,571 hr |
| V162-6.2 @ 145m | ~270 GWh | ~9.8% | ~5.9% | ~8.8% | ~226 GWh | ~31.9% | 2,795 hr |
| V163-4.5 @ 145m | ~232 GWh | ~9.2% | ~5.9% | ~8.8% | ~195 GWh | ~38.0% | 3,329 hr |
| V162-6.2 @ 125m | ~255 GWh | ~9.5% | ~5.9% | ~8.8% | ~214 GWh | ~30.2% | 2,645 hr |
| V163-4.5 @ 125m | ~220 GWh | ~8.9% | ~5.9% | ~8.8% | ~185 GWh | ~36.0% | 3,154 hr |

**Key insights**:
- Net production is ~75% of gross (Table 1 values)
- Wake losses dominate (~10%), then other losses (~9%), then sector (~6%)
- Nordex N164 still highest net production
- V162-6.2 @ 145m achieves ~96% of Nordex with better CF

---

## Files Already Created (Ready to Use)

1. ✅ `latam_hybrid/output/export.py` - Has `export_per_turbine_losses_table()` function
2. ✅ `latam_hybrid/claudedocs/loss_calculation_methodology.md` - Documentation
3. ✅ `tests/test_loss_calculations.py` - Unit tests (optional validation)
4. ✅ `scripts/plot_turbine_production_N164.py` - Visualization example (single config)

**STILL NEED TO CREATE**:
- ❌ `PowerCurve_analysis/scripts/power_curve_with_losses.py` - Main script for all 5 configs

---

## Script Template (for Step 1)

**Reference**: Use `scripts/plot_turbine_production_N164.py` as template

**Key differences for new script**:
- Loop through all 5 turbine configurations
- Use FULL dataset (not filtered to single year)
- Export to CSV tables (not plots)
- Save both summary table and per-turbine breakdowns

**Main structure**:
```python
TURBINE_CONFIGS = [
    {'name': 'Nordex N164 @ 164m', 'file': 'Nordex N164.csv', ...},
    {'name': 'V162-6.2 @ 145m', 'file': 'V162_6.2.csv', ...},
    # ... etc
]

results = []
for config in TURBINE_CONFIGS:
    # Load site with FULL wind data (no filtering)
    site = WindSite.from_file(...)

    # Run PyWake simulation
    result = (
        site
        .with_turbine(...)
        .set_layout(...)
        .set_sector_management(...)
        .run_simulation(wake_model='Bastankhah_Gaussian', compute_losses=True)
        .apply_losses(...)
        .calculate_production()
    )

    # Extract results
    results.append({...})

    # Export per-turbine breakdown
    export_per_turbine_losses_table(result, f"results/per_turbine_{config['name']}.csv")

# Save summary table
df = pd.DataFrame(results)
df.to_csv('results/table4_pywake_with_losses.csv', index=False)
```

---

## Quick Reference Commands

### Create Script
Use existing `scripts/plot_turbine_production_N164.py` as starting point

### Run Analysis in IPython
```bash
cd /mnt/c/Users/klaus/klauspython/Latam
ipython
%run PowerCurve_analysis/scripts/power_curve_with_losses.py
```

### Check Results
```bash
ls PowerCurve_analysis/results/
cat PowerCurve_analysis/results/table4_pywake_with_losses.csv
```

### Update Report
Open `PowerCurve_analysis/power_curve_analysis.md` and add section 1.2.4 + Table 4

### Generate Word Document
```bash
python PowerCurve_analysis/scripts/md_to_docx.py
```

---

## Benefits of This Update

✅ **Realistic production estimates** - Not just power curve application
✅ **Corrected sector losses** - Energy-based (5.87%) vs time-based (12.98%)
✅ **Corrected other losses** - 8.8% loss, not swapped
✅ **Wake modeling** - Accounts for turbine-to-turbine interactions
✅ **Per-turbine breakdowns** - Detailed loss analysis for each configuration
✅ **Professional tables** - Ready for reports and stakeholders
✅ **Validation** - Can compare gross (Table 1) vs net (Table 4)

---

## Notes

- **Full dataset required**: Using all 11.3 years (99,000 hours) for statistical accuracy
- **IPython recommended**: Faster execution, autoreload already configured
- **Runtime**: Plan for 20-30 minutes of simulation time
- **Validation**: Check sector losses are ~5-6%, not 12-13%
- **Documentation**: All methodology documented in `latam_hybrid/claudedocs/loss_calculation_methodology.md`

---

## Next Session Checklist

- [ ] Create `PowerCurve_analysis/scripts/power_curve_with_losses.py` based on template above
- [ ] Execute script in IPython (20-30 min runtime)
- [ ] Review generated CSV tables for correctness
- [ ] Update `power_curve_analysis.md` with section 1.2.4 and Table 4
- [ ] Regenerate Word document if needed
- [ ] Archive old results (if desired)
- [ ] Celebrate corrected analysis! 🎉
