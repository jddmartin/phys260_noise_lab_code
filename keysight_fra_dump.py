"""Utilities for getting a frequency response analysis (FRA) from a
Keysight scope"""

# For the format of the FRA data returned from scopes, see:
# "Keysight InfiniiVision 1200 X-Series and EDUX1052A/G Oscilloscopes,
# Programmer's guide" esp. Section 16, ":FRANalysis Commands"

import sys, os.path
import pyvisa
import warnings
warnings.simplefilter("ignore", UserWarning)
import matplotlib.pyplot as plt
import numpy as np

def get_fra_as_csv(inst):
    """Ask "inst" for FRA data and return resulting csv string"""
    inst.write(":FRANalysis:DATA?")
    a = inst.read_raw()
    expected_length = int(a[2:2+8])  # see Keysight programming manual
    full_str = a[int(chr(a[1]))+2:][:-1]  # last character is "\n".  ignore.
    csv_string = "".join([chr(x) for x in full_str])
    assert expected_length == len(csv_string)
    return csv_string


def parse_fra_csv(csvstring):
    """Parse csv string returned from FRA and return dictionary "d" with keys:
    "#", "freq_hz", "amp_vpp", "gain_db", "phase_deg"
    """
    lines = csvstring.split("\n")[:-1] # last line is empty.  ignore.
    d = {}
    d["#"], d["freq_hz"], d["amp_vpp"], d["gain_db"], d["phase_deg"] = (
        zip(*[[float(v) for v in line.split(",")] for line in lines[1:]]))
    return d


def write_fra_to_csv(inst, csvfilename):
    """Ask "inst" for FRA data and write csv file "csvfilename" and also
    return parsed data (see "parse_fra_csv")"""
    csv_string = get_fra_as_csv(inst)
    with open(csvfilename, "w") as f:
        f.write(csv_string)
    return parse_fra_csv(csv_string)


if __name__ == "__main__":
    # if run with no arguments returns the list of resources available
    
    rm = pyvisa.ResourceManager()    
    if len(sys.argv) == 1:  # no arguments; show available visa resources
        lor = rm.list_resources()
        print(f"list of resources: {lor=}")
        for r in lor:
            if "ASRL" in r:
                continue
            if "hislip0" in r:
                continue
            inst = rm.open_resource(r)
            print(f"opening: {inst=}")
            print(f"{r=} {inst.query('*IDN?')=}")
            inst.close()
        exit(0)
    
    if len(sys.argv) != 3:
        raise RuntimeError(
            "Provide two arguments: visa resource name and output filename.")
        exit(1)

    rs_name = sys.argv[1]
    csv_fname = sys.argv[2]
    
    if os.path.isfile(csv_fname):
        raise RuntimeError(f"File already exists: {csv_fname}")

    inst = rm.open_resource(rs_name)            
    data = write_fra_to_csv(inst, sys.argv[2])

    plt.plot(data["freq_hz"], data["gain_db"])
    ax = plt.gca()
    ax.set_xscale("log")
    plt.show()

