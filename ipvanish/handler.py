#!/usr/bin/env python3

import zipfile
import requests
import io
import os
import shutil
import tempfile
import re
import getpass
import math

from .settings import CONFIG_PATH, CONFIG_URL
from .utils import sort_vpn
from .vpn import IpvanishVPN


class IpvanishVPNHandler:

    def __init__(self):
        self.__config_list = os.listdir(os.path.join(CONFIG_PATH, "configs"))

    def get_ipvanish_config_list(self, countries=[]):
        if len(countries) > 0:
            L = []
            regex = r"ipvanish-("+r"|".join(countries)+r")-"
            for vpn in self.__config_list:
                if re.search(regex, vpn) is not None:
                    L.append(os.path.join(CONFIG_PATH, "configs",vpn))
            return L
        else:
            return [os.path.join(CONFIG_PATH, vpn) for vpn in self.__config_list]

    def update(self):
        with tempfile.TemporaryDirectory() as tmpfolder:
            try:
                r = requests.get(CONFIG_URL, stream=True)
                r.raise_for_status()
                z = zipfile.ZipFile(io.BytesIO(r.content))
                z.extractall(tmpfolder)
                tmp_config_content = os.listdir(tmpfolder)
                if len(tmp_config_content) == 0:
                    raise Exception("Empty folder")
                else:
                    shutil.rmtree(os.path.join(CONFIG_PATH, "configs"), ignore_errors=True)
                    shutil.copytree(
                        tmpfolder,
                        os.path.join(CONFIG_PATH, "configs")
                    )
            except:
                print("Failed to update vpn config")

    def connect(self, countries=[]):
        config_files = self.get_ipvanish_config_list(countries)
        if not os.path.exists(os.path.join(CONFIG_PATH, "auth")):
            username = getpass.getpass(prompt='Username: ')
            password = getpass.getpass(prompt="Password: ")
            with open(os.path.join(CONFIG_PATH, "auth"), "w") as auth:
                print(username, file=auth)
                print(password, file=auth)
        vpns = []
        for config_file in config_files:
            vpn = IpvanishVPN(config_file)
            vpns.append(vpn)

        if len(vpns) == 0:
            raise Exception("There is no available server")

        for vpn in vpns:
            t = vpn.get_ping()
            t.join()

        vpns.sort(key=sort_vpn)
        print([str(vpn) for vpn in vpns])
        vpns[0].connect()

