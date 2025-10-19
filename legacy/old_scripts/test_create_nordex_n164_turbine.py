import numpy as np
import pytest
from create_nordex_n164_turbine import create_nordex_n164_turbine


def test_create_nordex_n164_turbine_runs():
    # Should not raise
    turbine = create_nordex_n164_turbine()
    assert turbine is not None


def test_power_and_ct_ranges_and_shapes():
    turbine = create_nordex_n164_turbine()
    # Test with a range of wind speeds (including edge and mid values)
    test_ws = np.linspace(3, 26, 20)
    power = turbine.power(test_ws)
    ct = turbine.ct(test_ws)

    # Power should be between 0 and 7000 kW (in W)
    assert np.all(power >= 0)
    assert np.all(power <= 7000 * 1000)
    # Ct should be between 0 and 1
    assert np.all(ct >= 0)
    assert np.all(ct <= 1)
    # Output shapes should match input
    assert power.shape == test_ws.shape
    assert ct.shape == test_ws.shape


def test_power_and_ct_list_input():
    turbine = create_nordex_n164_turbine()
    test_ws = [5, 10, 15, 20, 25]
    power = turbine.power(test_ws)
    ct = turbine.ct(test_ws)
    assert isinstance(power, np.ndarray) or isinstance(power, list)
    assert isinstance(ct, np.ndarray) or isinstance(ct, list)
    assert len(power) == len(test_ws)
    assert len(ct) == len(test_ws) 