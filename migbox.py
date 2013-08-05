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
Can also run the command line interface or the sftp server.
"""

__version__ = 0.5
__author__ = 'Benjamin Ertl'

import os
import sys

from MiGBox.common import read_config, print_vars, get_vars 
from MiGBox.gui import AppUi 
from MiGBox import cli
from MiGBox.sftp import server

def start_server(args, basedir):
    if args.config:
        _vars = read_config(args.config, server=True)
    else:
        # try to read default configuration file at default location
        config = os.path.join(basedir, "config", "server.cfg")
        _vars = read_config(config, server=True)
        # command line parameters supercede config file parameters
        _vars["Connection"]["host"] = args.host if args.host else _vars["Connection"]["host"]
        _vars["Connection"]["port"] = args.port if args.port else _vars["Connection"]["port"]
        _vars["KeyAuth"]["hostkey"] = args.hostkey if args.hostkey else _vars["KeyAuth"]["hostkey"]
        _vars["KeyAuth"]["userkey"] = args.userkey if args.userkey else _vars["KeyAuth"]["userkey"]
        _vars["ROOT"]["rootpath"] = args.rootpath if args.rootpath else _vars["ROOT"]["rootpath"]
        _vars["Logging"]["logfile"] = args.logfile if args.logfile else _vars["Logging"]["logfile"]
        _vars["Logging"]["loglevel"] = args.loglevel if args.loglevel else _vars["Logging"]["loglevel"]
    if not os.path.isdir(_vars["ROOT"]["rootpath"]) or \
       not os.path.isfile(_vars["KeyAuth"]["hostkey"]) or \
       not os.path.isfile(_vars["KeyAuth"]["userkey"]):
        print_vars(_vars)
        print "Invalid server configuration!"
        sys.exit(1)
    if _vars["Logging"]["logfile"] and not os.path.isfile(_vars["Logging"]["logfile"]):
        _vars["Logging"]["logfile"] = None
    print_vars(_vars)
    server.run(**get_vars(_vars))

def start_cli(args, basedir):
    if args.config:
        _vars = read_config(args.config)
    else:
         # try to read default configuration file at default location
        config = os.path.join(basedir, "config", "migbox.cfg")
        _vars = read_config(config)
        # command line parameters supercede config file parameters
        _vars["Sync"]["source"] = args.source if args.source else _vars["Sync"]["source"]
        _vars["Sync"]["destination"] = args.destination \
                                    if args.destination else _vars["Sync"]["destination"]
        _vars["Connection"]["sftp_host"] = args.host if args.host else _vars["Connection"]["sftp_host"]
        _vars["Connection"]["sftp_port"] = args.port if args.port else _vars["Connection"]["sftp_port"]
        _vars["KeyAuth"]["hostkey"] = args.hostkey if args.hostkey else _vars["KeyAuth"]["hostkey"]
        _vars["KeyAuth"]["userkey"] = args.userkey if args.userkey else _vars["KeyAuth"]["userkey"]
        _vars["Mount"]["mountpath"] = args.mountpath if args.mountpath else _vars["Mount"]["mountpath"]
        _vars["Logging"]["logfile"] = args.logfile if args.logfile else _vars["Logging"]["logfile"]
        _vars["Logging"]["loglevel"] = args.loglevel if args.loglevel else _vars["Logging"]["loglevel"]
    mode = args.mode
    if mode == "local":
        if not os.path.isdir(_vars["Sync"]["source"]) or \
           not os.path.isdir(_vars["Sync"]["destination"]):
            print "Invalid source/destination path!"
            print_vars(_vars)
            sys.exit(1)
    else:
        if not os.path.isdir(_vars["Sync"]["source"]) or \
           not os.path.isdir(_vars["Mount"]["mountpath"]) or \
           not os.path.isfile(_vars["KeyAuth"]["hostkey"]) or \
           not os.path.isfile(_vars["KeyAuth"]["userkey"]):
            print "Invalid paths, check configuration!"
            print_vars(_vars)
            sys.exit(1)
    if _vars["Logging"]["logfile"] and not os.path.isfile(_vars["Logging"]["logfile"]):
        _vars["Logging"]["logfile"] = None
    print_vars(_vars)
    cli.run(mode, **get_vars(_vars))

def start_gui(args, basedir):
    # load configuration file at default location
    configfile = os.path.join(basedir, "config", "migbox.cfg")
    # get path to the gui icons
    icons_path = os.path.join(basedir, "icons")
    # set log file to default location
    logfile = os.path.join(basedir, "log", "sync.log")
    if args:
        if args.config:
            configfile = args.config
    if not os.path.isfile(configfile):
        # no configuration file found .. this will create a new empty
        # configuration file in the base directory.
        configfile = os.path.join(basedir, "migbox.cfg") 
    if not os.path.isfile(logfile):
        # no log file found .. this will create a new empty
        # log file in the base directory.
        logfile = os.path.join(basedir, "sync.log")
    AppUi.run(configfile, logfile, icons_path)

def _parseargs(basedir):
    from argparse import ArgumentParser

    parser = ArgumentParser(description="MiGBox file synchronization.")

    subparsers = parser.add_subparsers()

    guiparser = subparsers.add_parser("gui", help="start MiGBox (default)")
    guiparser.add_argument("-c", "--config", help="path to the MiGBox config file")
    guiparser.set_defaults(func=start_gui)

    cliparser = subparsers.add_parser("cli", help="start MiGBox console")
    cliparser.add_argument("mode", type=str, choices=['local', 'remote'],
                           help="synchronization mode")
    cliparser.add_argument("-c", "--config", help="path to the MiGBox config file")
    cliparser.add_argument("-src", "--source", help="source path for synchronization")
    cliparser.add_argument("-dst", "--destination", help="destination path for synchronization")
    cliparser.add_argument("-H", "--host", type=str, default="localhost",  help="host name or ip")
    cliparser.add_argument("-p", "--port", type=int, default=50007, help="host port number")
    cliparser.add_argument("-hk", "--hostkey", type=str, help="path to the server's public key")
    cliparser.add_argument("-uk", "--userkey", type=str, help="path to the user's private key")
    cliparser.add_argument("-m", "--mountpath", type=str, help="path to mount to via sftp")
    cliparser.add_argument("-l", "--logfile", type=str, help="path to the log file")
    cliparser.add_argument("-ll", "--loglevel", type=str, choices=['INFO', 'DEBUG'],
                              help="log level for logging")

    cliparser.set_defaults(func=start_cli)

    serverparser = subparsers.add_parser("server", help="start the  MiGBox server")
    serverparser.add_argument("-c", "--config", type=str, help="path to the server's config file")
    serverparser.add_argument("-H", "--host", type=str, help="host name or ip")
    serverparser.add_argument("-p", "--port", type=int, help="host port number")
    serverparser.add_argument("-hk", "--hostkey", type=str, help="path to the server's private key")
    serverparser.add_argument("-uk", "--userkey", type=str, help="path to the user's public key")
    serverparser.add_argument("-r", "--rootpath", type=str, help="root path of the server")
    serverparser.add_argument("-l", "--logfile", type=str, help="path to the log file")
    serverparser.add_argument("-ll", "--loglevel", type=str, choices=['INFO', 'DEBUG'],
                              help="log level for logging")

    serverparser.set_defaults(func=start_server)

    args = parser.parse_args()
    args.func(args, basedir)

def main():
    if getattr(sys, 'frozen', None):
        # modification for pyinstaller 2.0
        if hasattr(sys, "_MEIPASS"):
            basedir = sys._MEIPASS
        elif hasattr(sys, "executable"):
        # modification for cx_Freeze
            basedir = sys.executable
    else:
        # get path relative to migbox.py
        basedir = os.path.abspath(os.path.split(__file__)[0])
    if len(sys.argv) > 1:
        _parseargs(basedir)
    else:
        start_gui(None, basedir)

if __name__ == '__main__':
    main()
