"""Log RTD resistance and TEC current"""

# written by J. Martin, U Waterloo

import time, subprocess, os, argparse, csv, __main__
from datetime import datetime, timezone

import pyvisa
import numpy as np
np.set_printoptions(legacy='1.25')


def find_single_matching_visa_resource_name(device_description,
                                            requested_visa_name):
    """Helper function for acquiring a visa resource that looks for
    one and only one visa name that has the "requested_visa_name" within it.
    Throws exception if either no or more than one matching visa name
    is present.
    """

    rm = pyvisa.ResourceManager()        
    rs = rm.list_resources()

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
    debug = args["debug"]
    logfile = args["logfile"]
    
    pwr_supply_vname = find_single_matching_visa_resource_name(
        "power supply", args["pwr_supply_visa_resource_name"])

    dmm_vname = find_single_matching_visa_resource_name(
        "DMM", args["dmm_visa_resource_name"])

    first = True
    while True:
        if not first:
            first = False
            time.sleep(args["sleep_time"])            
            
        atime = time.time()
        utc_now = datetime.now().astimezone()
        utc_now_isoformat = utc_now.isoformat()

        rm = pyvisa.ResourceManager()        
        try:  # make power supply measurements:
            pwr_supply = rm.open_resource(pwr_supply_vname)
            current = float(pwr_supply.query("MEAS:CURR? CH1"))
            pwr.control_ren(6)            
            pwr.close()
        except:
            continue

        try:  # make resistance measurements:
            dmm = rm.open_resource(dmm_vname)
            resistance = float(dmm.query("MEAS:RES?"))
            dmm.control_ren(6)            
            dmm.close()
        except:
            continue
        
        print(
            f"{utc_now_isoformat=}, {atime=}, {resistance=}, {current=}")
        with open(logfile, "a", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(
                [utc_now_isoformat, atime, resistance, current,])


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
        "--sleep_time", float,
        help="sleep time (s) between measurements",
        default=10.0)
    
    parser.add_argument(
        "--pwr_supply_visa_resource_name", str,
        help="DMM visa resource name; can be partial",
        default="::0x2A8D::0x8F01::")
    
    parser.add_argument(
        "--dmm_visa_resource_name", str,
        help="DMM visa resource name; can be partial",
        default="::0x2A8D::0x1301::")

    parser.add_argument("logfile", type=str,
                        help = "log file to append to ",)

    return vars(parser.parse_args())  # return dictionary
        
if __name__ == "__main__":
    args = parse_args()
    main(args)
