"""Compute temperature corresponding to Pt1000 resistance"""

# uses results from here:
# https://en.wikipedia.org/wiki/Resistance_thermometer#Standard_resistance_thermometer_data


import sys
import numpy as np
np.set_printoptions(legacy='1.25')

def temp_for_rtd(rtd):
    """Calculate temperature in deg C given Pt1000 reading in ohms
    using https://en.wikipedia.org/wiki/Resistance_thermometer#Standard_resistance_thermometer_data
    """
    x = rtd / 1000.0
    a = 3.9083e-3
    b = -5.775e-7
    c = -4.183e-12

    t = (-a + np.sqrt(a**2 - 4 * b * (1 - x))) / (2.0 * b)
    return t

if __name__ == "__main__":
    resistance = float(sys.argv[1])
    temperature = temp_for_rtd(resistance)
    print(f"for {resistance=} (Ohms) {temperature=} (deg C)")
