import math
import os
import sys

# Adjust paths assuming this file is in backend/tests/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from backend.api.physics_utils import (
    calculate_pressure_altitude,
    calculate_isa_temperature,
    calculate_density_altitude,
    classify_vcbi_density_altitude,
    get_aviation_performance_impact
)

def test_calculate_pressure_altitude():
    assert abs(calculate_pressure_altitude(1013.25) - 0.0) < 0.1
    assert calculate_pressure_altitude(1000.0) > 0.0
    assert calculate_pressure_altitude(1020.0) < 0.0

def test_calculate_isa_temperature():
    assert abs(calculate_isa_temperature(0.0) - 15.0) < 0.1
    assert abs(calculate_isa_temperature(10000.0) - (-4.8)) < 0.1

def test_calculate_density_altitude():
    pa = 0.0
    isa = 15.0
    temp = 15.0
    assert abs(calculate_density_altitude(pa, temp, isa) - 0.0) < 0.1
    temp_hot = 30.0
    assert calculate_density_altitude(pa, temp_hot, isa) == 120.0 * 15.0

def test_classify_vcbi_density_altitude():
    assert classify_vcbi_density_altitude(1000.0) == "NORMAL"
    assert classify_vcbi_density_altitude(1868.2) == "NORMAL"
    assert classify_vcbi_density_altitude(1900.0) == "ELEVATED"
    assert classify_vcbi_density_altitude(2041.1) == "ELEVATED"
    assert classify_vcbi_density_altitude(2500.0) == "HIGH"

def test_get_aviation_performance_impact():
    assert "Standard performance" in get_aviation_performance_impact("NORMAL")
    assert "reduced climb performance" in get_aviation_performance_impact("ELEVATED")
    assert "Unusually high density altitude" in get_aviation_performance_impact("HIGH")
    assert get_aviation_performance_impact("INVALID") == "Unknown"

if __name__ == "__main__":
    test_calculate_pressure_altitude()
    test_calculate_isa_temperature()
    test_calculate_density_altitude()
    test_classify_vcbi_density_altitude()
    test_get_aviation_performance_impact()
    print("All tests passed!")
