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
            if arguments['command'] is None:
                self.parser.print_help()
            else:
                if arguments['command'] == 'update':
                    self.handler.update()
                elif arguments["command"] == 'connect':
                    self.handler.connect(arguments["countries"])
                else:
                    raise Exception("Unknown command")
        except Exception as e:
            print(e)
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
            "update",
            help="update ipvanish servers config files"
        )

        connect = command.add_parser(
            'connect',
            help='connect to server'
        )
        self.add_filters(connect.add_argument_group('filters'))

    def add_filters(self, parser):
        parser.add_argument(
            '--country',
            action='append',
            dest='countries',
            help="country name or code"
        )
