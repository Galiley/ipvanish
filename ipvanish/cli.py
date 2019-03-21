#!/usr/bin/env python3

import argparse


class IpVanishCli(object):
    def __init__(self):
        self._parser = IpvanishParser(
            "ipvanish",
            description=("Manage Ipvanish from the cli")
        )

    def run(self, args=None):
        arguments = vars(self._parser.parse_args(args))
        print(arguments)


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
        connect.add_argument(
            'settings',
            default=None,
            nargs="*"
        )
        self.add_filters(connect.add_argument_group('filters'))

        ping = command.add_parser(
            'ping',
            help='ping servers'
        )
        ping.add_argument(
            self.SUBCOMMAND,
            help="default: servers",
            default='servers',
            nargs="?",
            choices=['servers', 'countries', 'cities']
        )
        self.add_filters(ping.add_argument_group('filters'))

    def add_filters(self, parser):
        parser.add_argument(
            '--server',
            action='append',
            dest='servers',
            metavar="",
            help="server name or code"
        )
        parser.add_argument(
            '--country',
            action='append',
            dest='countries',
            metavar="",
            help="country name or code"
        )

        parser.add_argument(
            '--city',
            action='append',
            dest='cities',
            metavar="",
            help="city name"
        )
