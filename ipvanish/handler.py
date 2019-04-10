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
import datetime
import texttable

from .settings import CONFIG_PATH, CONFIG_URL
from .utils import sort_vpn
from .vpn import IpvanishVPN


class IpvanishVPNHandler:

    def get_ipvanish_config_list(self, countries=None):
        config_list = glob.glob(os.path.join(CONFIG_PATH, "configs", "*.ovpn"))
        if countries is not None:
            L = []
            regex = r"ipvanish-("+r"|".join(countries)+r")-"
            for vpn in config_list:
                if re.search(regex, vpn) is not None:
                    L.append(os.path.join(CONFIG_PATH, "configs",vpn))
            return L
        else:
            return [os.path.join(CONFIG_PATH, vpn) for vpn in config_list]

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

    def get_vpns(self, countries=None):
        config_files = self.get_ipvanish_config_list(countries)
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

        vpns = self.get_vpns(countries)
        vpns.sort(key=sort_vpn)
        print("Connecting to {} ...".format(vpns[0]))
        vpns[0].connect()

    def info(self, countries=None):
        vpns = self.get_vpns(countries)
        print("Possible available servers : {:n}".format(len(vpns)))
        ctime = os.path.getctime(os.path.join(CONFIG_PATH, "configs"))
        diff = datetime.datetime.now() - datetime.datetime.fromtimestamp(ctime)
        print("Last configs update : Less than {:n} days ago".format(diff.days + 1))

        vpns_dict = {}
        for vpn in vpns:
            if vpn.country_code not in vpns_dict:
                vpns_dict[vpn.country_code] = {}
            if vpn.town not in vpns_dict[vpn.country_code]:
                vpns_dict[vpn.country_code][vpn.town] = []
            vpns_dict[vpn.country_code][vpn.town].append((vpn.server,vpn.ping))

        table = texttable.Texttable(max_width=250)
        table.set_cols_align(['c', 'c', 'c', 'c'])
        table.set_cols_valign(['m', 'm', 'm', 'm'])
        table.add_rows([['Country code', 'Town', 'Server', "Ping"]])
        for country_code in vpns_dict:
            towns = ''
            servers = ''
            pings = ''
            nb_town = len(vpns_dict[country_code].keys())
            for town in vpns_dict[country_code]:
                towns += str(town)
                nb_server = len(vpns_dict[country_code][town])

                for (index_server, (server, ping)) in enumerate(vpns_dict[country_code][town], 0):
                    servers += str(server)
                    ping = ping if ping is not None else 'Unknown'
                    pings += str(ping)

                    if nb_server != 1 and (nb_server)>index_server:
                        pings+="\n"
                        servers+="\n"
                    if nb_town != 1 and (nb_server)>index_server:
                        towns+="\n"
            if nb_server!=1:
                towns="\n".join(towns.split("\n")[:-1])
                pings="\n".join(pings.split("\n")[:-1])
                servers="\n".join(servers.split("\n")[:-1])
            table.add_row([country_code, towns, servers, pings])
        print(table.draw())