#!/usr/bin/python
#
# MiGBox
#
# Copyright (C) 2013 Benjamin Ertl
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
MiGBox - File synchronization for the Minimum Intrusion Grid (MiG)

Runs by default the graphical user interface.
Can also run command line interface or sftp server.
"""

__version__ = 0.1
__author__ = 'Benjamin Ertl'

import sys

def start_server(args):
    print "Start server..."

def start_cli(args):
    print "Start console..."

def start_gui(args):
    print "Start gui..."

def _parseargs():
    from argparse import ArgumentParser

    parser = ArgumentParser(description="MiGBox file synchronization.")

    subparsers = parser.add_subparsers()

    guiparser = subparsers.add_parser("gui", help="start MiGBox (default)")
    guiparser.set_defaults(func=start_gui)

    cliparser = subparsers.add_parser("cli", help="start MiGBox console")
    cliparser.set_defaults(func=start_cli)

    serverparser = subparsers.add_parser("server", help="start MiGBox server")
    serverparser.add_argument("-c", "--config", help="server config file", \
                              action="store_true")
    serverparser.set_defaults(func=start_server)

    args = parser.parse_args()
    args.func(args)

if len(sys.argv) > 1:
    _parseargs()
else:
    start_gui(None)


