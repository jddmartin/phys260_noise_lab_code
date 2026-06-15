"""Vrms noise measurement averaging using Keysight DMM, 34461A"""

# written by J. Martin, U Waterloo

import pyvisa
import time
import numpy as np
import subprocess
import os

def main():
    rm = pyvisa.ResourceManager()
    rs = rm.list_resources()
    print(f"{rs=}")
    for r in rs:
        if "::0x2A8D::0x1301::" in r:  # VISA name for Keysight 34461A
            inst = rm.open_resource(r)
            break
    else:
        raise RuntimeError("Could not detect Keysight 34461A.  Is it connected?")
    try:
        print(inst.query("*IDN?"))    
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
        n_samples = 10
        inst.write("SAMPLE:COUNT " + str(n_samples))

        # make measurement:
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
        est_std_avg_vrms2 = np.sqrt(np.std(vals**2)**2 / (len(vals) - 1))

        # print results to screen:
        print(f"{time_elapsed_s=}")

    except:
        print("except")
        inst.control_ren(6)

    if os.name == "posix":  # "posix" is linux, "nt" is windows
        subprocess.call(["espeak", "I am finished, my friend."])

if __name__ == "__main__":
    # each sample takes 2.6 s
    
    main()
