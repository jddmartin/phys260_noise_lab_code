"""Vrms noise measurement averaging using Keysight DMM, 34461A"""

# written by J. Martin, U Waterloo

import time, subprocess, os, argparse, datetime, __main__

import pyvisa
import numpy as np
np.set_printoptions(legacy='1.25')

def main(args):
    n_samples = args["n_samples"]
    debug = args["debug"]

    rm = pyvisa.ResourceManager()
    rs = rm.list_resources()
    if debug: print(f"{rs=}")
    for r in rs:
        if "::0x2A8D::0x1301::" in r:  # VISA name for Keysight 34461A
            inst = rm.open_resource(r)
            break
    else:
        raise RuntimeError(
            "Could not detect Keysight 34461A.  Is it connected?")
    try:
        if debug: print(f'{inst.query("*IDN?")=}')    
        inst.timeout = 1000000

        # store the state of the instrument so that we go back to it after
        # finishing:
        inst.write(r'MMEM:STOR:STATE "INT:\JDDM"')

        # configure for measurement:
        inst.write("*RST")
        inst.write("*CLS")
        inst.write("TRIG:SOURCE IMMEDIATE")
        inst.write("CONF:VOLT:AC 1")
        
        inst.write("VOLT:AC:BAND 3") # 3 20 200
        inst.write("SAMPLE:COUNT " + str(n_samples))

        # make measurement:
        print("Measuring ...", n_samples, "samples, will take approximately: ",
              "%.1f" % (n_samples * 2.6),
              "(s) (=%.1f" % (n_samples * 2.6 / 60), "(min))")
        print("Turn volume up for audio alert when finished")
        start = time.time()
        while True:
            results = inst.query("READ?")
            stop = time.time()
            delta = stop-start
            break
        
        # return instrument back to original state:
        inst.write(r'MMEM:LOAD:STATE "INT:\JDDM"')    
        inst.write("SYST:LOC")

        # post process:
        time_elapsed_s = stop - start
        vals = np.array([float(x) for x in results.split(",")])
        avg_vrms2 = np.mean(vals**2)
        estimated_error_avg_vrms2 = (
            np.sqrt(np.std(vals**2)**2 / (len(vals) - 1)))

        # print results to screen:
        datestring = str(datetime.datetime.now().astimezone())
        print("\nSuccess! Finished at: " + datestring + "\n")
        print("\007")
        print(f"{time_elapsed_s=}")

        print(f"{np.sqrt(avg_vrms2)=} V")
        print()
        print(f"{avg_vrms2=} V^2")
        print(f"{estimated_error_avg_vrms2=} V^2")        

    except Exception as e:
        print(e)        
        inst.control_ren(6)

    if os.name == "posix":  # "posix" is linux, "nt" is windows
        subprocess.call(["espeak", "I am finished, my friend."])

def parse_args():
    example_of_use = "Example usage:\n " +  __main__.__file__ + " --debug 1"
    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog=example_of_use,
                                     formatter_class=
                                     argparse.RawTextHelpFormatter)
    parser.add_argument("--debug",
                        help = "print additional debug info ",
                        default=False, action="store_true")

    parser.add_argument("n_samples", type=int,
                        help = "number of samples ")

    return vars(parser.parse_args())  # return dictionary
        
if __name__ == "__main__":
    args = parse_args()
    main(args)
