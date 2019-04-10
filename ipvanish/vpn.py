#!/usr/bin/env python

import os
import subprocess
import re
import signal

from .utils import threaded
from .settings import CONFIG_PATH

class IpvanishVPN(object):

    def __init__(self, config_path):
        if not os.path.exists(config_path):
            raise ValueError("Invalid config path")

        self.config_path = config_path
        with open(config_path, 'r') as config_file:
            lines = config_file.readlines()

        self.config = {}
        for option in lines:
            option = option.split("\n")[0]
            args = option.split()
            if len(args) == 1:
                self.config[args[0]] = True
            else:
                self.config[args[0]] = args[1:]

        if not "remote" in self.config:
            raise("Invalid config file")

        self.ca = os.path.join(os.path.dirname(config_path),self.config['ca'][0])
        self.server = self.config["remote"][0]
        
        config_file_match = re.search(
            r"ipvanish-(?P<country>[A-Z]{2})-(?P<town>.*)-[a-z]{3}-[a-z0-9]{3}\.ovpn",
            os.path.basename(config_path)
        )

        self.country_code = None
        self.town = None
        if config_file_match is not None:
            self.country_code = config_file_match.group("country")
            self.town = " ".join(config_file_match.group("town").split("-"))
        self.ip = None
        self.ping = None
        self.proc = None

        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

    def __str__(self):
        if self.ip is not None:
            return "{} ({})".format(self.server, self.ip)
        else:
            return self.server

    def stop(self, signum, frame):
        if self.proc is not None:
            self.proc.kill()
    
    @threaded
    def ping_server(self):
        server = self.ip if self.ip is not None else self.server
        ping_process = subprocess.Popen(["ping", "-c2", "-w1", server], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = ping_process.communicate()
        if err:
            return None
        output = str(out)
        if self.ip is None:
            regex = r"PING "+r"\.".join(self.server.split("."))+r" \((?P<ip>[(\d{2})?.]+)\)"
            ip_match = re.search(regex, output)
            if ip_match is not None:
                self.ip = ip_match.group("ip")
        ping = None
        ping_match = re.search(r"rtt min/avg/max/mdev = [\d.]+/(?P<ping>[\d.]+)/[\d.]+/[\d.]+ ms", output)
        if ping_match is not None:
            ping = float(ping_match.group("ping"))
        self.ping = ping

    def connect(self):
        args = ['sudo','openvpn', "--config", self.config_path, '--auth-user-pass', os.path.join(CONFIG_PATH, 'auth'), "--ca", self.ca]
        self.proc = subprocess.Popen(args)
        self.proc.wait()

