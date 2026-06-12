"""Preliminary noise measurement using Keysight DMM, 34461A"""

import pyvisa
import time
import numpy as np
import subprocess

rm = pyvisa.ResourceManager()
rs = rm.list_resources()
print(f"{rs=}")
for r in rs:
    if "::0x2A8D::0x1301::" in r:
        inst = rm.open_resource(r)
        break
else:
    raise RuntimeError("Crap!")
try:
    print(inst.query("*IDN?"))    
    inst.timeout = 1000000
    inst.write(r'MMEM:STOR:STATE "INT:\JDDM"')
    inst.write("*RST")
    inst.write("*CLS")
    inst.write("TRIG:SOURCE IMMEDIATE")
    inst.write("CONF:VOLT:AC 1")
#    inst.write("TRIG:DEL 0")
    inst.write("VOLT:AC:BAND 3") # 3 20 200
    nsamp = 100
    inst.write("SAMPLE:COUNT " + str(nsamp))
    start = time.time()
    while True:
        results = inst.query("READ?")
        stop = time.time()
#        print(f"{start=} {stop=}")
        delta = stop-start
        print(f"{delta=}")
        print(f"{delta/nsamp=}")    
#        print(results)
        break
    vals = np.array([float(x) for x in results.split(",")])
    print(str(np.mean(vals**2)) + ",",
          np.sqrt(np.std(vals**2)**2 / (len(vals) - 1)))
    inst.write(r'MMEM:LOAD:STATE "INT:\JDDM"')    
    inst.write("SYST:LOC")
except:
    print("except")
    inst.control_ren(6)
subprocess.call(["espeak", "I am finished, my friend."])
