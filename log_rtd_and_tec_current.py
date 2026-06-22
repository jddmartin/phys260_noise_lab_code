"""Log RTD resistance and TEC current"""

# written by J. Martin, U Waterloo

import time, subprocess, os, argparse, csv, __main__
from datetime import datetime, timezone

import pyvisa
import numpy as np
np.set_printoptions(legacy='1.25')

def main(args):
    debug = args["debug"]
    logfile = args["logfile"]

    while True:
        rm = pyvisa.ResourceManager()        
        rs = rm.list_resources()
        if debug: print(f"{rs=}")
        try:
            for r in rs:
                if "::0x2A8D::0x8F01::" in r:  # VISA name for Keysight EDU36311A
                    inst_pwr = rm.open_resource(r)
                    break
            else:
                raise RuntimeError(
                    "Could not detect Keysight EDU36311A.  Is it connected?")
            for r in rs:
                if "::0x2A8D::0x1301::" in r:  # VISA name for Keysight 34461A
                    inst_dmm = rm.open_resource(r)
                    break
            else:
                raise RuntimeError(
                    "Could not detect Keysight 34461A.  Is it connected?")
            atime = time.time()
            utc_now = datetime.now().astimezone()
            utc_now_isoformat = utc_now.isoformat()
            resistance = float(inst_dmm.query("MEAS:RES?"))
            
            # CURR? gives setpoint, even when output is disabled,
            # whereas MEAS:CURR? gives actual current
            # current = float(inst_pwr.query("CURR? (@1)"))
            current = float(inst_pwr.query("MEAS:CURR? CH1"))
            print(
                f"{utc_now_isoformat=}, {atime=}, {resistance=}, {current=}")
            with open(logfile, "a", newline="") as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(
                    [utc_now_isoformat, atime, resistance, current,])


        except Exception as e:
            print(e)

        inst_pwr.control_ren(6)            
        inst_pwr.close()

        inst_dmm.control_ren(6)
        inst_dmm.close()

        time.sleep(10)            


def parse_args():
    example_of_use = "Example usage:\n " +  __main__.__file__ + " --debug 1"
    parser = argparse.ArgumentParser(description=__doc__,
                                     epilog=example_of_use,
                                     formatter_class=
                                     argparse.RawTextHelpFormatter)
    parser.add_argument("--debug",
                        help = "print additional debug info ",
                        default=False, action="store_true")

    parser.add_argument("logfile", type=str,
                        help = "log file to append to ",)

    return vars(parser.parse_args())  # return dictionary
        
if __name__ == "__main__":
    args = parse_args()
    main(args)
