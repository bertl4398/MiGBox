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
Provides a SFTP server to run on the MiG server or an other central server for
synchronization.
"""

__version__ = 0.3
__author__ = 'Benjamin Ertl'

import sys, time, threading, socket, os
import traceback
import json

import paramiko

import delta

from ConfigParser import ConfigParser

from stub_sftp import StubServer, StubSFTPServer

CMD_BLOCKCHK = 205
CMD_DELTA = 206
CMD_PATCH = 207

class SFTPServer(paramiko.SFTPServer):
    """
    This class inherits from L{paramiko.SFTPServer}.

    It is required here to overwrite/extend the paramiko.SFTPServer. 
    """
    def __init__(self, channel, name, server, \
                 sftp_si=paramiko.SFTPServerInterface, *largs, **kwargs):
        paramiko.SFTPServer.__init__(self, channel, name, server, \
                                     sftp_si, *largs, **kwargs)

    def _process(self, t, request_number, msg):
        """
        Overwritten method for processing incoming requests to except
        and execute synchronization specific requests.

        This is a hook into the paramiko.SFTPServer implementation

        See L{paramiko.SFTPServer._process}
        """
        if t == CMD_BLOCKCHK:
            path = msg.get_string()
            bs = delta.blockchksums(self.server._realpath(path))
            j = json.dumps(bs)
            message = paramiko.Message()
            message.add_int(request_number)
            message.add_string(j)
            self._send_packet(t, str(message))
            return
        elif t == CMD_DELTA:
            path = msg.get_string()
            bs = json.loads(msg.get_string())
            d = delta.delta(self.server._realpath(path), bs)
            j = json.dumps(d)
            message = paramiko.Message()
            message.add_int(request_number)
            message.add_string(j)
            self._send_packet(t, str(message))
        elif t == CMD_PATCH:
            path = msg.get_string()
            d = json.loads(msg.get_string())
            delta.patch(self.server._realpath(path), d)
            self._send_status(request_number, self.server.rename(path + ".patched", path))
        else:
            return paramiko.SFTPServer._process(self, t, request_number, msg)

def main():
    """
    Main entry point to run the sftp server.
    """
    config = ConfigParser()
    config.read('server.cfg')

    host = config.get('Connection', 'sftp_host')
    port = config.getint('Connection', 'sftp_port')
    backlog = config.getint('Connection', 'sftp_backlog')

    log_file = config.get('Logging', 'log_file')
    log_level = config.get('Logging', 'log_level')

    paramiko.util.log_to_file(log_file, log_level)

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
