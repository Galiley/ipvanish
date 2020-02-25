import os
import subprocess
import re
import signal


class IpvanishError(Exception):
    pass


class IpvanishVPN:
    def __init__(self, ovpn_path, geojson={}):
        if not os.path.exists(ovpn_path):
            raise IpvanishError("Invalid path to ovpn config file")

        self.ovpn_path = ovpn_path
        self.geojson = geojson

        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

        self.ping = float("inf")
        self.proc = None

        # Retrieve data from geojson
        self.countryCode = self.geojson.get("countryCode", None)
        self.city = self.geojson.get("city", None)
        self.ip = self.geojson.get("ip", None)
        self.capacity = self.geojson.get("capacity", float("inf"))
        self.country = self.geojson.get("country", None)
        self.region = self.geojson.get("continent", None)

        # Parse ovpn file
        with open(ovpn_path, "r") as config_file:
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
            raise IpvanishError("Invalid config file")

        if self.config["auth-user-pass"] == True:
            self.config["auth-user-pass"] = [
                os.path.join(os.path.dirname(os.path.dirname(self.ovpn_path)), "auth")
            ]

        if self.config["ca"] == ["ca.ipvanish.com.crt"]:
            self.config["ca"][0] = os.path.join(
                os.path.dirname(ovpn_path), self.config["ca"][0]
            )

        # Retrive data from ovpn if not find in the geojson
        self.server = self.ip if self.ip is not None else self.config["remote"][0]

        if self.countryCode is None or self.city is None:
            config_file_match = re.search(
                r"ipvanish-(?P<country>[A-Z]{2})-(?P<city>.*)-[a-z]{3}-[a-z0-9]{3}\.ovpn",
                os.path.basename(ovpn_path),
            )
            if config_file_match is not None:
                self.countryCode = config_file_match.group("country")
                self.city = " ".join(config_file_match.group("city").split("-"))

    def to_dict(self):
        return {
            "server": self.server,
            "city": self.city,
            "country": self.country if self.country else self.countryCode,
            "region": self.region,
            "capacity": f"{self.capacity} %",
            "ping": f"{self.ping} ms",
        }

    def __str__(self):
        return f"<IpvanishVPN({', '.join([f'{k} = {v}' for k,v in self.to_dict().items()])})>"

    def __repr__(self):
        return str(self)

    def __lt__(self, other):
        return [self.ping, self.capacity, self.server] < [
            other.ping,
            other.capacity,
            other.server,
        ]

    def __le__(self, other):
        return not self.__gt__(other)

    def __eq__(self, other):
        return [self.ping, self.capacity, self.server] == [
            other.ping,
            other.capacity,
            other.server,
        ]

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        return [self.ping, self.capacity, self.server] > [
            other.ping,
            other.capacity,
            other.server,
        ]

    def __ge__(self, other):
        return not self.__lt__(other)

    def stop(self, signum, frame):
        if self.proc is not None:
            self.proc.kill()

    def ping_server(self):
        ping_process = subprocess.Popen(
            ["ping", "-c3", "-w1", self.server],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = ping_process.communicate()
        if err:
            self.ping = float("inf")
            return
        output = str(out)
        ping = float("inf")
        ping_match = re.search(
            r"rtt min/avg/max/mdev = [\d.]+/(?P<ping>[\d.]+)/[\d.]+/[\d.]+ ms", output
        )
        if ping_match is not None:
            ping = int(float(ping_match.group("ping")))
        self.ping = ping

    def _generate_openvpn_arguments(self):
        args = []
        for key, value in self.config.items():
            args.append(f"--{key}")
            if value != True:
                args.extend(value)
        return args

    def connect(self):
        args = ["sudo", "openvpn"]
        args.extend(self._generate_openvpn_arguments())
        self.proc = subprocess.Popen(args)
        self.proc.wait()
