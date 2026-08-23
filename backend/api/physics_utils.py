import math

def calculate_pressure_altitude(qnh_hpa: float) -> float:
    """
    Calculates Pressure Altitude (PA) in feet.
    Formula: PA = 145366.45 * [1 - (QNH / 1013.25)^0.190284]
    """
    if qnh_hpa <= 0:
        return 0.0
    return 145366.45 * (1 - math.pow(qnh_hpa / 1013.25, 0.190284))

def calculate_isa_temperature(pa_ft: float) -> float:
    """
    Calculates International Standard Atmosphere (ISA) Temperature in Celsius at a given Pressure Altitude.
    Formula: T_ISA = 15 - 1.98 * (PA / 1000)
    """
    return 15.0 - 1.98 * (pa_ft / 1000.0)

def calculate_density_altitude(pa_ft: float, actual_temp_c: float, isa_temp_c: float) -> float:
    """
    Calculates Density Altitude (DA) in feet.
    Formula: DA = PA + 120 * (T_actual - T_ISA)
    """
    return pa_ft + 120.0 * (actual_temp_c - isa_temp_c)

def classify_vcbi_density_altitude(da_ft: float, p75: float = 1868.2, p90: float = 2041.1) -> str:
    """
    Classifies VCBI Density Altitude into NORMAL, ELEVATED, or HIGH based on historical percentiles.
    """
    if da_ft <= p75:
        return "NORMAL"
    elif da_ft <= p90:
        return "ELEVATED"
    else:
        return "HIGH"

def get_aviation_performance_impact(classification: str) -> str:
    """
    Returns a description of the potential aviation performance impact based on DA classification.
    """
    if classification == "NORMAL":
        return "Standard performance expected. No significant density altitude limitations."
    elif classification == "ELEVATED":
        return "Slightly reduced climb performance and longer take-off rolls expected."
    elif classification == "HIGH":
        return "Unusually high density altitude relative to historical VCBI conditions. Aircraft take-off and climb performance may be notably affected."
    return "Unknown"
