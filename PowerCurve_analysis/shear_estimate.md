# Wind Shear Coefficient Estimation

## Data Source
Wind speed data obtained from **Global Wind Atlas** at the project location.

## Reference Conditions
- **Reference Height (H_ref)**: 100 m
- **Reference Wind Speed (V_ref)**: 7.11 m/s

## Measurement Data

| Height (m) | Wind Speed (m/s) |
|------------|------------------|
| 50         | 6.28             |
| 100        | 7.11             |
| 150        | 7.66             |
| 200        | 8.10             |

## Power Law Model
The wind shear is modeled using the power law equation:

```
V/V_ref = (H/H_ref)^α
```

Where:
- V = wind speed at height H
- V_ref = reference wind speed at height H_ref
- α (alpha) = wind shear coefficient

## Calculated Results

### Wind Shear Coefficient (Alpha)

**Recommended value: α = 0.1846**

#### Calculation Methods

1. **Individual Point Calculation** (excluding reference point)
   - H = 50 m: α = 0.1791
   - H = 150 m: α = 0.1838
   - H = 200 m: α = 0.1881
   - **Mean: α = 0.1836 ± 0.0037**

2. **Least Squares Fit** (all points)
   - **Best-fit: α = 0.1846 ± 0.0023**
   - R² = 0.9995 (excellent fit)

3. **Linear Regression** (log-log transformation)
   - α = 0.1830
   - Intercept = 0.0016 (≈0, as expected)

### Model Validation

| Height (m) | Actual (m/s) | Predicted (m/s) | Error (%) |
|------------|--------------|-----------------|-----------|
| 50         | 6.28         | 6.26            | -0.38%    |
| 100        | 7.11         | 7.11            | 0.00%     |
| 150        | 7.66         | 7.66            | 0.03%     |
| 200        | 8.10         | 8.08            | -0.24%    |

**Maximum prediction error: < 0.4%**

## Terrain Classification

**Alpha value: 0.1846** → **Moderately rough terrain**

### Comparison with Standard Values

| Alpha Value | Terrain Type                              |
|-------------|-------------------------------------------|
| 0.143 (1/7) | Smooth/flat terrain (neutral stability)   |
| **0.185**   | **Your site (moderately rough terrain)**  |
| 0.20        | Moderately rough (crops, obstacles)       |
| 0.30        | Very rough terrain/urban areas            |

## Wind Speed Extrapolation

Using the calculated alpha value (α = 0.1846), wind speeds at various heights:

| Height (m) | Wind Speed (m/s) | Notes           |
|------------|------------------|-----------------|
| 10         | 4.65             |                 |
| 30         | 5.69             |                 |
| 50         | 6.28             | Measured        |
| 80         | 6.82             | Hub height      |
| 100        | 7.11             | Reference       |
| 120        | 7.35             |                 |
| 150        | 7.66             | Measured        |
| 200        | 8.08             | Measured        |

## Conclusion

The wind shear coefficient for the project location is **α = 0.1846**, indicating moderately rough terrain with scattered obstacles. This value provides excellent agreement with the Global Wind Atlas data (R² = 0.9995) and can be used for extrapolating wind speeds to turbine hub heights.

---

**Analysis Date**: October 18, 2025
**Data Source**: Global Wind Atlas
**Calculation Method**: Power law regression with least squares fitting
