"""Compute temperature corresponding to Pt1000 resistance"""

# uses results from here:
# https://en.wikipedia.org/wiki/Resistance_thermometer#Standard_resistance_thermometer_data


import sys, argparse, __main__
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


def main(args):
    resistance = float(args["resistance"])
    temperature = temp_for_rtd(resistance)
    print(f"for {resistance=} (Ohms)\n{temperature=} (deg C)")


def parse_args():
#    example_of_use = "Example usage:\n " +  __main__.__file__ + " --debug 1"
    example_of_use = ""
    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog=example_of_use,
                                     formatter_class=
                                     argparse.RawTextHelpFormatter)
    parser.add_argument("--debug",
                        help = "print additional debug info ",
                        default=False, action="store_true")

    parser.add_argument("resistance", type=float,
                        help = "Pt1000 resistance in ohms ")

    return vars(parser.parse_args())  # return dictionary


if __name__ == "__main__":
    args = parse_args()
    main(args)
    
