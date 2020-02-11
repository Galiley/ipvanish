#!/usr/bin/env python
import argparse
import os
import sys
import traceback

from ipvanish.handler import IpvanishVPNHandler
from ipvanish.error import IpvanishError


class IpVanishCli(object):
    def __init__(self):
        self.parser = IpvanishParser(
            "ipvanish", description=("Manage Ipvanish from the cli")
        )

        self.handler = IpvanishVPNHandler()

    def run(self, args=None):
        try:
            arguments = vars(self.parser.parse_args(args))
            if "countries" in arguments:
                L = []
                for args in arguments["countries"]:
                    if isinstance(args, list):
                        L.extend(args)
                    else:
                        L.append(args)

                # Patch United Kingdom/ Great Britain
                if "UK" in L:
                    L.append("GB")
                elif "GB" in L:
                    L.append("UK")
                arguments["countries"] = L
            if arguments["version"]:
                from ipvanish import __version__

                print(__version__)
                sys.exit(0)
            if arguments["command"] is None:
                raise IpvanishError("You need to specify the command")
            else:
                if arguments["command"] == "sync":
                    self.handler.sync()
                elif arguments["command"] == "connect":
                    self.handler.connect(arguments["countries"])
                elif arguments["command"] == "auth":
                    self.handler.auth()
                else:
                    raise IpvanishError("Unknown command")
        except IpvanishError as e:
            print(e, file=sys.stderr)
            self.parser.print_help()
        except Exception:
            traceback.print_exc()


class IpvanishParser(argparse.ArgumentParser):
    COMMAND = "command"
    SUBCOMMAND = "filter"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_argument(
            "-v",
            "--version",
            action="store_true",
            help="Print %(prog)s version then exit",
        )

        command = self.add_subparsers(
            dest=self.COMMAND, parser_class=argparse.ArgumentParser
        )

        command.add_parser("sync", help="Sync ipvanish vpn servers config files")

        command.add_parser("auth", help="Edit auth file for ipvanish vpn servers")

        connect = command.add_parser(
            "connect", help="Connect to an ipvanish vpn server"
        )
        self.add_filters(connect.add_argument_group("filters"))

    def add_filters(self, parser):
        parser.add_argument(
            "--country",
            action="append",
            dest="countries",
            nargs="+",
            help="Filter vpn server by country code",
            default=[],
        )
