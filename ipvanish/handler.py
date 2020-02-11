#!/usr/bin/env python
import zipfile
import requests
import io
import os
import shutil
import tempfile
import re
import getpass
import glob
import multiprocessing as mp

from ipvanish.vpn import IpvanishVPN
from ipvanish.error import IpvanishError


class IpvanishVPNHandler:

    ipvanishPath = os.path.expanduser("~/.config/ipvanish")
    configURL = "https://www.ipvanish.com/software/configs/configs.zip"
    geojsonURL = "https://www.ipvanish.com/api/servers.geojson"

    def _get_ipvanish_config_list(self, countries=[]):
        config_list = glob.glob(os.path.join(self.ipvanishPath, "configs", "*.ovpn"))
        if len(countries) > 0:
            L = []
            regex = r"ipvanish-(" + r"|".join(countries) + r")-"
            for vpn in config_list:
                if re.search(regex, vpn) is not None:
                    L.append(os.path.join(self.ipvanishPath, "configs", vpn))
            return L
        else:
            return [os.path.join(self.ipvanishPath, vpn) for vpn in config_list]

    def sync(self):
        with tempfile.TemporaryDirectory() as tmpfolder:
            try:
                r = requests.get(self.configURL, stream=True)
                r.raise_for_status()
                z = zipfile.ZipFile(io.BytesIO(r.content))
                z.extractall(tmpfolder)
                tmp_config_content = os.listdir(tmpfolder)
                if len(tmp_config_content) == 0:
                    raise IpvanishError("Empty folder")
                else:
                    shutil.rmtree(
                        os.path.join(self.ipvanishPath, "configs"), ignore_errors=True
                    )
                    shutil.copytree(
                        tmpfolder, os.path.join(self.ipvanishPath, "configs")
                    )
                    print("Ipvanish config lists downloaded")
            except:
                raise IpvanishError("Failed to update vpn config")

    def _get_ipvanish_geojson(self, countries):
        r = requests.get(self.geojsonURL)
        if r.status_code == 200:
            data = r.json()
            if countries:
                data = list(
                    filter(lambda x: x["properties"]["countryCode"] in countries, data)
                )
            d = {}
            for geo in data:
                properties = geo["properties"]
                countryCode = properties["countryCode"]
                if countryCode == "GB":
                    countryCode = "UK"
                city = properties["city"].replace(" ", "-")
                hostNameId = properties["hostname"].split(".")[0]
                key = f"ipvanish-{countryCode}-{city}-{hostNameId}"
                d[key] = properties
            return d
        return {}

    def _get_vpns(self, countries=None):
        config_files = self._get_ipvanish_config_list(countries)
        if len(config_files) == 0:
            raise IpvanishError("There is no available server")

        geojson_data = self._get_ipvanish_geojson(countries)
        vpns = []
        threads = []
        for config_file in config_files:
            geojson_id = config_file.split(".ovpn")[0].split("/")[-1]
            vpn = IpvanishVPN(config_file, geojson_data.get(geojson_id, {}))
            vpns.append(vpn)
            thread = vpn.ping_server()
            threads.append(thread)

        for thread in threads:
            thread.join()
        vpns.sort()
        return vpns

    def auth(self):
        username = getpass.getpass(prompt="Ipvanish's username: ")
        password = getpass.getpass(prompt="Ipvanish's password: ")
        with open(os.path.join(self.ipvanishPath, "auth"), "w") as auth:
            print(username, file=auth)
            print(password, file=auth)

    def connect(self, countries=None):
        if not os.path.exists(os.path.join(self.ipvanishPath, "configs")):
            self.sync()

        if not os.path.exists(os.path.join(self.ipvanishPath, "auth")):
            self.auth()

        vpns = self._get_vpns(countries)
        print(f"Connecting to {vpns[0]} ...")
        vpns[0].connect()
