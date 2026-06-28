"""Vrms noise measurement averaging using Keysight DMM, 34461A"""

# written by J. Martin, U Waterloo

import time, subprocess, os, os.path, argparse, csv, __main__
from datetime import datetime, timezone

import pyvisa
import numpy as np
np.set_printoptions(legacy='1.25')

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
    debug = args["debug"]    
    n_samples = args["n_samples"]
    logfile = args["logfile"]
    repeat = args["repeat"]
    comment =args["comment"]

    dmm_vname = find_single_matching_visa_resource_name(
        "DMM", args["dmm_visa_resource_name"], debug=debug)
    if debug:
        print(f"found {dmm_vname=}")

    rm = pyvisa.ResourceManager()

    while True:
        try:  # make DMM measurements:
            dmm = rm.open_resource(dmm_vname)
            dmm.timeout = int(1000 * n_samples * 2.6 * 1.5)

            # store the state of the instrument so that we go back to it after
            # finishing:
            dmm.write(r'MMEM:STOR:STATE "INT:\JDDM"')

            # configure for measurement:
            dmm.write("*RST")
            dmm.write("*CLS")
            dmm.write("TRIG:SOURCE IMMEDIATE")
            dmm.write("CONF:VOLT:AC 1")

            dmm.write("VOLT:AC:BAND 3") # 3 20 200
            dmm.write("SAMPLE:COUNT " + str(n_samples))

            # make measurement:
            print("Measuring ...", n_samples,
                  "samples, will take approximately: ",
                  "%.1f" % (n_samples * 2.6),
                  "(s) (=%.1f" % (n_samples * 2.6 / 60), "(min))")
            print("Turn volume up for audio alert when finished")
            start = time.time()
            utc_now = datetime.now().astimezone()
            utc_now_isoformat = utc_now.isoformat()

            while True:
                results = dmm.query("READ?")
                stop = time.time()
                delta = stop-start
                break

            # return instrument back to original state:
            dmm.write(r'MMEM:LOAD:STATE "INT:\JDDM"')    
            dmm.write("SYST:LOC")
            dmm.close()
            
        except pyvisa.errors.VisaIOError as e:
            print("dmm busy? skipping, will retry ...")
            continue
            

        # post process:
        time_elapsed_s = stop - start
        vals = np.array([float(x) for x in results.split(",")])
        avg_vrms2 = np.mean(vals**2)
        sqrt_avg_vrms2 = np.sqrt(avg_vrms2)
        estimated_error_avg_vrms2 = (
            np.sqrt(np.std(vals**2)**2 / (len(vals) - 1)))

        # print results to screen:
        datestring = str(datetime.now().astimezone())
        print("\nSuccess! Finished at: " + datestring)
        print(f"{time_elapsed_s=}")
        print(f"{np.sqrt(avg_vrms2)=} V")
        print(f"{avg_vrms2=} V^2")
        print(f"{estimated_error_avg_vrms2=} V^2")        

        if os.name == "posix":  # "posix" is linux, "nt" is windows
            subprocess.call(["espeak", "I am finished, my friend."])
        else:
            print("\007")

        with open(logfile, "a", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(
                [utc_now_isoformat, start,
                 comment,
                 len(vals),
                 sqrt_avg_vrms2,                 
                 avg_vrms2,
                 estimated_error_avg_vrms2,
                 ])
        if not repeat:
            break

            
def parse_args():
    example_of_use = "Example usage:\n " +  __main__.__file__ + " --debug"
    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog=example_of_use,
                                     formatter_class=
                                     argparse.RawTextHelpFormatter)
    parser.add_argument("--debug",
                        help = "print additional debug info ",
                        default=False, action="store_true")

    parser.add_argument(
        "--dmm_visa_resource_name", type=str,
        help="DMM visa resource name; can be partial",
        default="::0x2A8D::0x1301::")
    
    parser.add_argument("--repeat",
                        help = "repeat measurements, writing to csv file ",
                        default=False, action="store_true")

    parser.add_argument("--n_samples", type=int,
                        help = "number of samples ",
                        default=1)

    main_filename_base, _ = os.path.splitext(
        os.path.split(__main__.__file__)[-1])
    parser.add_argument("--logfile", type=str,
                        help = "log file to append to ",
                        default=(main_filename_base+".csv"))

    parser.add_argument(
        "--comment", type=str,
        help="comment to write to *.csv",
        default="")


    return vars(parser.parse_args())  # return dictionary
        
if __name__ == "__main__":
    args = parse_args()
    main(args)
