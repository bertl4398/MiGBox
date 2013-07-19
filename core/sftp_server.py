#!/usr/bin/python
#
# SFTP server based on paramiko
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
SFTP server implementation based on paramiko.
Provides a SFTP server to run on the MiG server or other central server for
synchronization.
"""

__version__ = 0.2
__author__ = 'Benjamin Ertl'

import sys, time, threading, socket
import traceback
import ConfigParser
import hashlib

import paramiko

from stub_sftp import StubServer, StubSFTPServer

class SFTPServer(paramiko.SFTPServer):
    def __init__(self, channel, name, server, \
                 sftp_si=paramiko.SFTPServerInterface, *largs, **kwargs):
        paramiko.SFTPServer.__init__(self, channel, name, server, \
                                     sftp_si, *largs, **kwargs)

    def _process(self, t, request_number, msg):
        if t == 205:
            md5 = hashlib.md5()
            md5.update(msg.get_string())
            message = paramiko.Message()
            message.add_int(request_number)
            message.add_string(md5.hexdigest())
            paramiko.SFTPServer._send_packet(self, t, str(message))
            #paramiko.SFTPServer._send_status(self, request_number, 0)
            return
        else:
            return paramiko.SFTPServer._process(self, t, request_number, msg)

def main():
    config = ConfigParser.ConfigParser()
    config.read('server.cfg')

    host = config.get('Connection', 'host')
    port = int(config.get('Connection', 'port'))
    backlog = int(config.get('Connection', 'backlog'))

    log_level = config.get('Logging', 'level')
    log_level = 'DEBUG'
    paramiko.common.logging.basicConfig(level=getattr(paramiko.common,log_level))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    s.bind((host,port))
    s.listen(backlog)
    t = None

    try:
        while True:
            conn, addr = s.accept()

            t= paramiko.Transport(conn)

            prvkey = config.get('KeyAuth', 'prvkey')
            t.add_server_key(paramiko.RSAKey.from_private_key_file(prvkey))

            event = threading.Event()
            server = StubServer()

            t.set_subsystem_handler('sftp', SFTPServer, StubSFTPServer)

            t.start_server(event, server)

            while t.is_active():
                time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
    finally:
        s.close()
        if t:
            t.close()

    sys.exit(0)

if __name__ == '__main__':
    main()
