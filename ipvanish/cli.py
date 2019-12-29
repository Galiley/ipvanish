#!/usr/bin/env python3

import argparse
import os
import sys
import traceback

from .handler import IpvanishVPNHandler

class IpVanishCli(object):
    def __init__(self):
        self.parser = IpvanishParser(
            "ipvanish",
            description=("Manage Ipvanish from the cli")
        )

        self.handler = IpvanishVPNHandler()
    
    def run(self, args=None):
        try:
            arguments = vars(self.parser.parse_args(args))
            if "countries" in arguments:
                L = []
                for args in arguments['countries']:
                    if isinstance(args, list):
                        L = L+args
                    else:
                        L.append(args)
                arguments['countries'] = L
            if arguments['command'] is None:
                self.parser.print_help()
            else:
                if arguments['command'] == 'sync':
                    self.handler.sync()
                elif arguments["command"] == 'connect':
                    self.handler.connect(arguments["countries"])
                else:
                    raise Exception("Unknown command")
        except Exception as e:
            self.parser.print_help()


class IpvanishParser(argparse.ArgumentParser):
    COMMAND = "command"
    SUBCOMMAND = "filter"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        command = self.add_subparsers(
            dest=self.COMMAND,
            parser_class=argparse.ArgumentParser
        )

        command.add_parser(
            "sync",
            help="Sync ipvanish servers config files"
        )

        connect = command.add_parser(
            'connect',
            help='Connect to an ipvanish vpn server'
        )
        self.add_filters(connect.add_argument_group('filters'))

    def add_filters(self, parser):
        parser.add_argument(
            '--country',
            action='append',
            dest='countries',
            nargs='+',
            help="country name or code",
            default=[]
        )
