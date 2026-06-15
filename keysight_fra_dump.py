"""Get frequency response analysis (FRA) from a Keysight DSOX1102G \
oscilloscope
"""

# For the format of the FRA data returned from scopes, see:
# "Keysight InfiniiVision 1200 X-Series and EDUX1052A/G Oscilloscopes,
# Programmer's guide" esp. Section 16, ":FRANalysis Commands"

import sys, os.path, argparse, __main__
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

def main(args):
    csv_fname = args["csv_filename"]    
    
    rm = pyvisa.ResourceManager()    
    rs = rm.list_resources()

    for r in rs:
        if "::0x2A8D::0x1797::" in r:  # VISA name for Keysight DSOX1102G
            inst = rm.open_resource(r)
            break
    else:
        raise RuntimeError(
            "Could not detect Keysight scope.  Is it connected?")
     
    if os.path.isfile(csv_fname):
        raise RuntimeError(f"File already exists: {csv_fname}")

    data = write_fra_to_csv(inst, csv_fname)

    # plot data:
    plt.plot(data["freq_hz"], data["gain_db"])
    ax = plt.gca()
    ax.set_xscale("log")
    ax.set_xlabel("frequency (Hz)")
    ax.set_ylabel("voltage gain (dB)")
    plt.show()

def parse_args():
    example_of_use = "Example usage:\n " +  __main__.__file__ + " --debug 1"
    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog=example_of_use,
                                     formatter_class=
                                     argparse.RawTextHelpFormatter)
    parser.add_argument("--debug",
                        help = "print additional debug info ",
                        default=False, action="store_true")

    parser.add_argument("csv_filename", type=str,
                        help = "filename for csv output")

    return vars(parser.parse_args())  # return dictionary
        
if __name__ == "__main__":
    args = parse_args()
    main(args)
