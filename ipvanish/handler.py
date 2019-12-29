#!/usr/bin/env python3

import zipfile
import requests
import io
import os
import shutil
import tempfile
import re
import getpass
import glob

from .settings import CONFIG_PATH, CONFIG_URL
from .vpn import IpvanishVPN


class IpvanishVPNHandler:

    def _get_ipvanish_config_list(self, countries=[]):
        config_list = glob.glob(os.path.join(CONFIG_PATH, "configs", "*.ovpn"))
        if len(countries) > 0:
            L = []
            regex = r"ipvanish-("+r"|".join(countries)+r")-"
            for vpn in config_list:
                if re.search(regex, vpn) is not None:
                    L.append(os.path.join(CONFIG_PATH, "configs",vpn))
            return L
        else:
            return [os.path.join(CONFIG_PATH, vpn) for vpn in config_list]

    def sync(self):
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

    def _get_vpns(self, countries=None):
        config_files = self._get_ipvanish_config_list(countries)
        if len(config_files) == 0:
            raise Exception("There is no available server")
        
        vpns = []
        threads = []
        for config_file in config_files:
            vpn = IpvanishVPN(config_file)
            vpns.append(vpn)
            thread = vpn.ping_server()
            threads.append(thread)

        for thread in threads:
            thread.join()

        return vpns


    def connect(self, countries=None):
        if not os.path.exists(os.path.join(CONFIG_PATH, "auth")):
            username = getpass.getpass(prompt='Username: ')
            password = getpass.getpass(prompt="Password: ")
            with open(os.path.join(CONFIG_PATH, "auth"), "w") as auth:
                print(username, file=auth)
                print(password, file=auth)

        vpns = self._get_vpns(countries)
        vpns.sort()
        print("Connecting to {} ...".format(vpns[0]))
        vpns[0].connect()