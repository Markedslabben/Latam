# PowerCurve Analysis - Development Log

## Session: 2025-10-20

### Objective
Create stacked bar charts showing per-turbine annual energy production with detailed loss breakdown for Nordex N164 wind turbines.

---

## Work Completed

### 1. Fixed PyWake Time Series Aggregation Issue
**Problem**: PyWake's `.aep()` method returns hourly timeseries `(n_turbines, n_timesteps)` for time series simulations, not annual totals.

**Solution**: Created `_get_aep_per_turbine()` helper method that properly aggregates:
```python
# site.py:708-727
def _get_aep_per_turbine(self, sim_result) -> np.ndarray:
    aep_raw = sim_result.aep()
    if len(aep_raw.shape) == 2:
        # Timeseries: sum over time dimension
        return aep_raw.sum(dim='time').values  # (n_turbines,)
    else:
        # Weibull: already aggregated
        return aep_raw.values
```

**Impact**: Fixed "Turbine 113880" bug where script was iterating over 113,880 hourly timesteps instead of 13 turbines.

---

### 2. Implemented Per-Turbine Loss Calculation
**Architecture**: Modified simulation workflow to calculate TRUE per-turbine losses (not just farm averages).

**Implementation** (site.py:302-341):
- Run **2 PyWake simulations**:
  1. **With wake model**: Get actual production per turbine
  2. **Without wake model**: Get ideal production per turbine
- Calculate per-turbine losses in correct cascade:
  ```
  Ideal (no losses)
    ↓ Wake losses = Ideal - Production_with_wake
  Production with wake
    ↓ Sector losses = Production_with_wake × (1 - availability_factor)
  Production with wake + sector
    ↓ Other losses = Production_with_wake_and_sector × loss_percentage
  Net production (all losses applied)
  ```

**Loss Prevention**: Each loss calculated on remaining energy after previous losses (no amplification).

**Stored in Metadata**:
```python
result.metadata['ideal_per_turbine_gwh']        # List[float], shape (13,)
result.metadata['wake_loss_per_turbine_gwh']    # List[float], shape (13,)
result.metadata['sector_loss_per_turbine_gwh']  # List[float], shape (13,)
result.metadata['other_loss_per_turbine_gwh']   # List[float], shape (13,)
result.turbine_production_gwh                    # List[float], shape (13,) - Net
```

All values in **absolute GWh/yr per turbine** (not percentages).

---

### 3. Updated Sector Management Loss Tracking
**Enhancement**: Modified `_apply_sector_management_to_results()` to return per-turbine sector losses:
```python
# site.py:729-795
def _apply_sector_management_to_results(
    self, sim_result, wind_direction_bins, return_losses=False
):
    # Calculate sector loss before applying curtailment
    sector_loss_per_turbine[turbine_idx] = original_aep * (1 - avail_factor)
    # Apply curtailment
    aep_per_turbine[turbine_idx] *= avail_factor

    if return_losses:
        return aep_per_turbine, sector_loss_per_turbine
```

**Current Configuration**: 6 turbines restricted to 120° sectors (33% availability → 67% losses).

---

### 4. Updated Plot Script for New Loss Structure
**Script**: `scripts/plot_turbine_production_N164.py`

**Changes**:
- Extract per-turbine losses from metadata (lines 136-140)
- Create stacked bar chart with proper ordering (bottom → top):
  1. Net production (sky blue) - with GWh/yr labels
  2. Other losses (violet) - with % in legend
  3. Sector management losses (moss green) - with % in legend
  4. Wake losses (orange) - with % in legend

**Data Flow**:
```python
ideal_per_turbine_gwh = result.metadata['ideal_per_turbine_gwh']
wake_loss_per_turbine = result.metadata['wake_loss_per_turbine_gwh']
sector_loss_per_turbine = result.metadata['sector_loss_per_turbine_gwh']
other_loss_per_turbine = result.metadata['other_loss_per_turbine_gwh']
turbine_production_net = result.turbine_production_gwh
```

---

### 5. PyWake Result Object Preservation
**Enhancement**: Store PyWake simulation result object in metadata for advanced access:
```python
# site.py:335
'pywake_sim_result': sim_res  # Full xarray SimulationResult object
```

**Accessible Data**:
```python
pywake_sim = result.metadata['pywake_sim_result']
ws = pywake_sim.WS.values           # Wind speed timeseries (8760,)
ti = pywake_sim.TI.values           # Turbulence intensity (8760,)
power = pywake_sim.Power.values     # Power per turbine (13, 8760)
ws_eff = pywake_sim.WS_eff.values   # Effective WS per turbine (13, 8760)
ti_eff = pywake_sim.TI_eff.values   # Effective TI per turbine (13, 8760)
```

---

## Current Status

### ✅ Completed
- [x] Fix PyWake timeseries aggregation bug
- [x] Implement per-turbine loss calculation architecture
- [x] Add per-turbine wake losses (TRUE variation by position)
- [x] Add per-turbine sector losses (TRUE variation by restrictions)
- [x] Add per-turbine other losses (uniform percentage)
- [x] Store all losses in absolute GWh/yr format
- [x] Update plot script to use new metadata structure
- [x] Preserve PyWake result object for advanced access

### 🔄 In Progress
- [ ] **Complete simulation run** - Simulation currently running in background (process b4323f)
  - Started: 2025-10-20 session
  - Expected duration: 10-15 minutes for dual PyWake simulations
  - Process: `/mnt/c/Users/klaus/anaconda3/envs/latam/python.exe scripts/plot_turbine_production_N164.py`
- [ ] **Verify stacked bar chart** - Need to confirm correct visual output after simulation completes
- [ ] **Debug any visualization issues** - Ensure proper stacking order and labels

---

## Next Steps

### 1. Complete Current Simulation (Timeseries Method)
**Action**:
- Run `scripts/plot_turbine_production_N164.py` to completion
- Verify output plot at `latam_hybrid/claudedocs/Production_per_turbine_N164_timeseries.png`
- Check that stacked bars show correct order and values

**Expected Output**:
- 13 bars (one per turbine)
- Each bar stacked (bottom → top): Net → Other → Sector → Wake
- Net production labeled with GWh/yr values
- Loss segments labeled with percentages in legend

**Alternative**: Run in IPython for faster execution:
```python
%run scripts/plot_turbine_production_N164.py
```

---

### 2. Verify Loss Calculations
**Validation Checks**:
```python
# After simulation completes
ideal = np.array(result.metadata['ideal_per_turbine_gwh'])
wake = np.array(result.metadata['wake_loss_per_turbine_gwh'])
sector = np.array(result.metadata['sector_loss_per_turbine_gwh'])
other = np.array(result.metadata['other_loss_per_turbine_gwh'])
net = np.array(result.turbine_production_gwh)

# Check: ideal - wake - sector - other ≈ net
residual = ideal - wake - sector - other - net
print(f"Max residual: {np.max(np.abs(residual)):.6f} GWh")  # Should be ~0
```

**Expected Results**:
- Unrestricted turbines (2,4,6,8,10,11,13): sector_loss = 0 GWh
- Restricted turbines (1,3,5,7,9,12): sector_loss ≈ 67% of (ideal - wake)
- All turbines: other_loss ≈ 8.8% of (ideal - wake - sector)

---

### 3. Create Weibull Distribution Version
**Goal**: Repeat analysis using Weibull distribution method instead of timeseries.

**New Script**: `scripts/plot_turbine_production_N164_weibull.py`

**Key Changes**:
```python
# Change simulation method from 'timeseries' to 'weibull'
result = (
    site
    .run_simulation(
        wake_model='Bastankhah_Gaussian',
        simulation_method='weibull',  # ← Changed from 'timeseries'
        wind_direction_bins=12,        # Required for Weibull
        compute_losses=True
    )
    .apply_losses(loss_config_file=str(losses_path))
    .calculate_production()
)
```

**Benefits of Weibull**:
- Much faster computation (~30 seconds vs 3+ minutes)
- Uses wind frequency bins instead of hourly timesteps
- Good for quick analysis and parameter studies

**Output**: `Production_per_turbine_N164_weibull.png`

---

### 4. Compare Timeseries vs Weibull Results
**Analysis**: Create comparison table showing AEP differences:

| Metric | Timeseries | Weibull | Difference |
|--------|-----------|---------|------------|
| Total AEP (GWh/yr) | TBD | TBD | TBD |
| Wake losses (%) | TBD | TBD | TBD |
| Sector losses (%) | TBD | TBD | TBD |
| Capacity Factor (%) | TBD | TBD | TBD |

**Expected**: Small differences (<2%) due to time aggregation effects.

---

### 5. Update Documentation
**Files to Update**:

1. **`latam_hybrid/docs/README.md`**
   - Add section on per-turbine loss calculation
   - Document metadata fields for loss arrays
   - Explain timeseries vs Weibull methods

2. **`latam_hybrid/claudedocs/wind_losses_implementation_summary.md`**
   - Update with per-turbine loss calculation architecture
   - Add examples of accessing per-turbine data
   - Document PyWake result object preservation

3. **`scripts/README.md`** (create if needed)
   - Document plotting scripts
   - Usage instructions for timeseries vs Weibull
   - Expected outputs and interpretation

---

## Technical Notes

### Performance Optimization
- **Timeseries simulation**: ~3-6 minutes (2 sims × 8760 timesteps × 13 turbines)
- **Weibull simulation**: ~30-60 seconds (12 direction bins)
- Running via IPython is ~2x faster than via Claude (no startup overhead)

### Known Issues
1. **WSL → Windows performance**: File I/O across boundary adds latency
2. **Module import overhead**: Fresh Python process loads all libraries from disk
3. **Simulation taking 9+ minutes**: Currently running 2 PyWake simulations sequentially

### Sector Management Configuration
```python
# 6 turbines restricted to 60-120° and 240-300° (120° total out of 360°)
# Availability: 33.3% → Sector losses: ~67% for restricted turbines
# Farm-level sector losses: ~13.7%
```

---

## Data Validation

### Example Per-Turbine Values (Expected)
```python
# Turbine 1 (restricted, upwind):
ideal: 28.5 GWh/yr
wake_loss: 2.0 GWh/yr (7% - upwind position)
sector_loss: 17.8 GWh/yr (67% of remaining - restricted)
other_loss: 0.8 GWh/yr (8.8% of remaining)
net: 7.9 GWh/yr

# Turbine 2 (unrestricted, upwind):
ideal: 28.3 GWh/yr
wake_loss: 1.9 GWh/yr (7% - upwind)
sector_loss: 0.0 GWh/yr (unrestricted)
other_loss: 2.3 GWh/yr (8.8% of remaining)
net: 24.1 GWh/yr
```

---

## Files Modified

### Core Framework
- `latam_hybrid/wind/site.py` - Added per-turbine loss calculation
  - Lines 302-341: Dual simulation and loss extraction
  - Lines 708-727: `_get_aep_per_turbine()` helper
  - Lines 729-795: Enhanced sector management with loss tracking
  - Lines 441-470: Per-turbine other losses in `apply_losses()`

### Plotting Scripts
- `scripts/plot_turbine_production_N164.py` - Updated to use new metadata structure
  - Lines 133-163: Extract per-turbine losses from metadata
  - Lines 186-211: Stacked bar chart with value labels

### Test Scripts
- `scripts/test_timeseries_N164.py` - Fixed array flattening issue
  - Lines 170-181: Proper per-turbine display (not timesteps)

---

## Git Status
```
Modified:
  latam_hybrid/wind/site.py
  scripts/plot_turbine_production_N164.py
  scripts/test_timeseries_N164.py

To be created:
  PowerCurve_analysis/log.md (this file)
  scripts/plot_turbine_production_N164_weibull.py (next step)
```

---

## Session End Notes

**Date**: 2025-10-20
**Time spent**: ~3 hours
**Main achievement**: Implemented true per-turbine loss calculation with correct loss cascade

### Status at Session End
- ✅ Code implementation complete (site.py, plot script)
- 🔄 Simulation running in background (process b4323f)
- ⏳ Plot generation pending simulation completion
- 📝 Documentation updated

### Blocker Resolution
**Original issue**: Simulation taking 9+ minutes via Claude
**Analysis**: WSL→Windows boundary + module import overhead + dual simulations
**Recommendation**: Run in IPython for faster iteration (~2x speed improvement)

### Next Session Checklist
1. **Check simulation status**: `BashOutput b4323f` or verify plot exists
2. **Verify plot output**: Check `latam_hybrid/claudedocs/Production_per_turbine_N164_timeseries.png`
3. **Validate results**:
   - 13 turbine bars
   - Correct stacking order (net→other→sector→wake)
   - Reasonable GWh/yr values (~20-25 GWh mean)
4. **Create Weibull version**: Duplicate script with `simulation_method='weibull'`
5. **Compare methods**: Timeseries vs Weibull accuracy and speed
6. **Update documentation**: README.md, implementation summary, scripts README
