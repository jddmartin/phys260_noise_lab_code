"""Sets output current on EDU36311A channel 1"""

# written by J. Martin, U Waterloo

import time, subprocess, os, argparse, datetime, __main__

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
    command = args["command"]
    print(f"{command=}")
    debug = args["debug"]

    pwr_supp_vname = find_single_matching_visa_resource_name(
        "power supply", args["pwr_supp_visa_resource_name"], debug=debug)
    if debug:
        print(f"found {pwr_supp_vname=}")

    rm = pyvisa.ResourceManager()

    inst = rm.open_resource(pwr_supp_vname)

    try:
        if debug: print(f'{inst.query("*IDN?")=}')
        inst.timeout = 1000000

        if command == "tec_current":
            current = args["current"]
            inst.write("VOLT 6, (@1)")
            command_string = r"CURR " + f"{current:.3f}" +r", (@1)"
            print(command_string)
            resp = inst.write(command_string)
            print(f"{resp=}")
        elif command == "nab_config":
            inst.write("VOLT 15, (@2)")
            inst.write("CURR 0.050, (@2)")
            inst.write("VOLT 15, (@3)")
            inst.write("CURR 0.050, (@3)")

    except Exception as e:
        print(e)
    finally:
        inst.control_ren(6)

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
        "--pwr_supp_visa_resource_name", type=str,
        help="Power supply visa resource name; can be partial",
        default="::0x2A8D::0x8F01::")


    subparsers = parser.add_subparsers(help="sub-command help",
        dest="command",  # will hold subcommand name as string
        required=True)   # make sub-command required,
                         # see: https://stackoverflow.com/a/55834365

    # tec_current
    parser_tec_current = subparsers.add_parser(
        "tec_current", help="help for get")
    parser_tec_current.add_argument("current", type=float,
                        help = "output current (A) ")

    # +/-15 V noise amplifier box (nab) supply config
    parser_set = subparsers.add_parser("nab_config", help="help for set")

    return vars(parser.parse_args())  # return dictionary

if __name__ == "__main__":
    args = parse_args()
    main(args)
