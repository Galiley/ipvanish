#!/usr/bin/env python3

import os
import sys

from ipvanish.cli import IpVanishCli

if __name__ == "__main__":
    if os.geteuid() !=0:
        sys.exit("This programm need to be run as root")

    ipvanish = IpVanishCli()
    ipvanish.run()