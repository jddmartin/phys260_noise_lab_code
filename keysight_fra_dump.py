"""Get frequency response analysis (FRA) from a Keysight DSOX1102G \
oscilloscope
"""

# written by J. Martin, U Waterloo

# For the format of the FRA data returned from scopes, see:
# "Keysight InfiniiVision 1200 X-Series and EDUX1052A/G Oscilloscopes,
# Programmer's guide" esp. Section 16, ":FRANalysis Commands"

import sys, os, os.path, argparse, csv, __main__
from datetime import datetime, timezone
import pyvisa
import warnings
warnings.simplefilter("ignore", UserWarning)
import matplotlib.pyplot as plt
import numpy as np
np.set_printoptions(legacy='1.25')
import pandas as pd
import scipy.integrate as si

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

def read_edu1052g_bode(afilename):
    df = pd.read_csv(afilename, encoding = "ISO-8859-1")
    fs = df[df.keys()[1]].to_numpy()
    gains = df[df.keys()[3]].to_numpy()
    phases = np.unwrap(df[df.keys()[4]].to_numpy(), period=360)
    return dict(fs=fs, gains=gains, phases=phases)


def find_single_matching_visa_resource_name(device_description,
                                            requested_visa_name,
                                            debug=False):
    """Helper function for acquiring a visa resource that looks for
    one and only one visa name that has the "requested_visa_name" within it.
    Throws exception if either no or more than one matching visa resource
    is present.
    """

    rm = pyvisa.ResourceManager()        
    rs = rm.list_resources()

    if debug:
        print(f"found resources {rs=}")

    n_found = 0
    for r in rs:
        if requested_visa_name in r:
            n_found += 1
            vname = r # lock visaname we use
            
    if n_found == 0:
        error_message = (
            f"No {device_description} found in "
            +f"visa resources: {rs}")            
        raise RuntimeError(error_message)

    elif n_found > 1:
        error_message = (
            f"More than one {device_description} found in "
            +f"visa resources: {rs}")    
        raise RuntimeError(error_message)

    return vname


def main(args):
    dump_csv_fname = args["dump_csv_filename"]    
    logfile = args["logfile"]
    
    oscope_vname = find_single_matching_visa_resource_name(
        "oscilloscope", args["oscope_visa_resource_name"], debug=debug)
    if debug:
        print(f"found {oscope_vname=}")

    rm = pyvisa.ResourceManager()            
    oscope = rm.open_resource(oscope_vname)    
     
    if os.path.isfile(dump_csv_fname):
        raise RuntimeError(f"File already exists: {dump_csv_fname}")

    start = time.time()
    utc_now = datetime.now().astimezone()
    utc_now_isoformat = utc_now.isoformat()
    
    data = write_fra_to_csv(oscope, dump_csv_fname)

    sys = read_edu1052g_bode(dump_csv_fname)
    print("\nSuccess! Finished at: " + utc_now_isoformat)
    print(f"{min(sys['fs'])=}, {max(sys['fs'])=}, {len(sys['fs'])=},")
    tv_corr_gain = 10**(sys["gains"]/20)
    noise_bandwidth = si.simpson(tv_corr_gain**2, x=sys["fs"])
    print(f"{noise_bandwidth=:.6g} Hz")
    print("Close figure window to finish.")

    with open(logfile, "a", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(
            [utc_now_isoformat, start, dump_csv_fname,
             comment,
             noise_bandwidth,
             ])

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

    parser.add_argument(
        "--oscope_visa_resource_name", type=str,
        help="oscilloscope visa resource name; can be partial",
        default="::0x2A8D::0x1797::")

    main_filename_base, _ = os.path.splitext(
        os.path.split(__main__.__file__)[-1])
    parser.add_argument("--logfile", type=str,
                        help = "log file to append to ",
                        default=(main_filename_base+".csv"))

    parser.add_argument(
        "--comment", type=str,
        help="comment to write to .csv logfile",
        default="")

    parser.add_argument("csv_filename", type=str,
                        help = "csv filename for dumped output")

    return vars(parser.parse_args())  # return dictionary
        
if __name__ == "__main__":
    args = parse_args()
    main(args)
