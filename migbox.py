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

__version__ = 0.3
__author__ = 'Benjamin Ertl'

import os
import sys

from ConfigParser import SafeConfigParser

from MiGBox.gui import ui
from MiGBox import cli
from MiGBox.sftp import server

def check_server_args(host, port, backlog, hostkey, userkey, root_path, log_file, log_level):
    # TODO check valid host
    if not port > 0 and port < 65535:
        print "Port number out of range"
        sys.exit(1)
    if not backlog > 0 and backlog < 10:
        print "Backlog min: 1, max: 10"
        sys.exit(1) 
    if not hostkey:
        print "No host key specified .. trying default path 'keys/server_rsa_key'"
        hostkey = os.path.abspath('keys/server_rsa_key')
    if not userkey: 
        print "No user key specified .. trying default path 'keys/user_rsa_key.pub'"
        userkey = os.path.abspath('keys/user_rsa_key.pub')
    if not root_path:
        print "No root path specified .. using default path 'tests/remote'"
        root_path = os.path.abspath('tests/remote')
    if not log_file:
        print "No log path specified .. using default path 'log/server.log'"
        log_file = os.path.abspath('log/server.log')
    if not log_level:
        print "No log level specified .. using default level 'INFO'"
        log_level = 'INFO'

    if not os.path.exists(hostkey):
        print "Could not find host key, please specify!"
        sys.exit(1)
    if not os.path.exists(userkey):
        print "Could not find user key, please specify!"
        sys.exit(1)
    if not os.path.exists(root_path):
        print "Could not find root path, please specify!"
        sys.exit(1)
    if not os.path.exists(log_file):
        print "Could not find log path, please specify!"
        sys.exit(1)

    print """
Using host      {0}
Using port      {1}
Using host key  {2}
Using user key  {3}
Using root path {4}
Using log path  {5}
Using log level {6}
""".format(host, port, hostkey, userkey, root_path, log_file, log_level)

    return [host, port, backlog, hostkey, userkey, root_path, log_file, log_level]

def start_server(args):

    if args.config:
        config = SafeConfigParser()
        config.read(args.config)

        host = config.get("Connection", "sftp_host")
        port = config.getint("Connection", "sftp_port")
        backlog = config.getint("Connection", "sftp_backlog")
        hostkey = config.get("KeyAuth", "hostkey")
        userkey = config.get("KeyAuth", "userkey")
        root_path = config.get("ROOT", "root_path")
        log_file = config.get("Logging", "log_file")
        log_level = config.get("Logging", "log_level")

    else:
        host = args.host
        port = args.port
        backlog = 10
        hostkey = args.hostkey
        userkey = args.userkey
        root_path = args.root
        log_file = args.log
        log_level = args.loglevel

    server.run(
        *check_server_args(host, port, backlog, hostkey, userkey, root_path, log_file, log_level))

def check_cli_args(mode, src, dst, host, port, hostkey, userkey, log_file, log_level, mountpath):
    if not src:
        print "No source path specified .. using default path 'tests/local'"
        src = os.path.abspath('tests/local')
    if mode == 'local' and not dst:
        print "No destination path specified .. using default path 'tests/remote'"
        dst = os.path.abspath('tests/remote')
    if mode == 'remote':
        # TODO check valid host name/ip
        if not port > 0 and port < 65535:
            print "Port number out of range"
            sys.exit(1)
        if not hostkey:
            print "No host key specified .. trying default path 'keys/server_rsa_key.pub'"
            hostkey = os.path.abspath('keys/server_rsa_key.pub')
        if not userkey: 
            print "No user key specified .. trying default path 'keys/user_rsa_key'"
            userkey = os.path.abspath('keys/user_rsa_key')
        if not mountpath:
            print "No mount path specified .. trying default path 'mount/'"
            mountpath = os.path.abspath('mount')
    if not log_file:
        print "No log path specified .. using default path 'log/sync.log'"
        log_file = os.path.abspath('log/sync.log')
    if not log_level:
        print "No log level specified .. using default level 'INFO'"
        log_level = 'INFO'

    if not os.path.exists(src):
        print "Could not find source path, please specify!"
        sys.exit(1)
    if mode == 'local' and not os.path.exists(dst):
        print "Could not find destination path, please specify!"
        sys.exit(1)
    if mode == 'remote':
        if not os.path.exists(hostkey):
            print "Could not find host key, please specify!"
            sys.exit(1)
        if not os.path.exists(userkey):
            print "Could not find user key, please specify!"
            sys.exit(1)
        if not os.path.exists(mountpath):
            print "Could not find mount path, please specify!"
            sys.exit(1)
    if not os.path.exists(log_file):
        print "Could not find log path, please specify!"
        sys.exit(1)

    if mode == 'local':
        print """
Using source      {0}
Using destination {1}
Using log path    {2}
Using log level   {3}
""".format(src, dst, log_file, log_level)
    elif mode == 'remote':
        print """
Using source    {0}
Using host      {1}
Using port      {2}
Using host key  {3}
Using user key  {4}
Using log path  {5}
Using log level {6}
""".format(src, host, port, hostkey, userkey, log_file, log_level)

    return [mode, src, dst, host, port, hostkey, userkey, log_file, log_level, mountpath]

def start_cli(args):
    if args.config:
        config = SafeConfigParser()
        config.read(args.config)
        src = config.get("Sync", "sync_src")
        dst = config.get("Sync", "sync_dst")
        host = config.get("Connection", "sftp_host")
        port = config.getint("Connection", "sftp_port")
        hostkey = config.get("KeyAuth", "hostkey")
        userkey = config.get("KeyAuth", "userkey")
        log_file = config.get("Logging", "log_file")
        log_level = config.get("Logging", "log_level")
        mountpath = config.get("Mount", "mountpath")
    else:
        src = args.source
        dst = args.destination
        host = args.host
        port = args.port
        hostkey = args.hostkey
        userkey = args.userkey
        log_file = args.log
        log_level = args.loglevel
        mountpath = args.mountpath

    mode = args.mode

    cli.run(*check_cli_args(mode, src, dst, host, port, hostkey,
                            userkey, log_file, log_level,mountpath))

def start_gui(args):
    if args:
        if args.config:
            ui.run(args.config)
    ui.run()

def _parseargs():
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
    cliparser.add_argument("-l", "--log", type=str, help="path to the log file")
    cliparser.add_argument("-ll", "--loglevel", type=str, choices=['INFO', 'DEBUG'],
                              help="log level for logging")

    cliparser.set_defaults(func=start_cli)

    serverparser = subparsers.add_parser("server", help="start the  MiGBox server")
    serverparser.add_argument("-c", "--config", help="path to the server's config file")
    serverparser.add_argument("-H", "--host", type=str, default="localhost",  help="host name or ip")
    serverparser.add_argument("-p", "--port", type=int, default=50007, help="host port number")
    serverparser.add_argument("-hk", "--hostkey", type=str, help="path to the server's private key")
    serverparser.add_argument("-uk", "--userkey", type=str, help="path to the user's public key")
    serverparser.add_argument("-r", "--root", type=str, help="root path of the server")
    serverparser.add_argument("-l", "--log", type=str, help="path to the log file")
    serverparser.add_argument("-ll", "--loglevel", type=str, choices=['INFO', 'DEBUG'],
                              help="log level for logging")

    serverparser.set_defaults(func=start_server)

    args = parser.parse_args()
    print args
    args.func(args)

def main():
    os.environ['MIGBOXPATH'] = os.path.abspath(os.curdir)
    if len(sys.argv) > 1:
        _parseargs()
    else:
        start_gui(None)

if __name__ == '__main__':
    main()


