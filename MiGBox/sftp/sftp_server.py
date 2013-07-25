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

HEADER = """
SFTP server for MiGBox - version {0}
Copyright (c) 2013 {1}

MiGBox comes with ABSOLUTELY NO WARRANTY. This is free software,
and you are welcome to redistribute it under certain conditions.

type 'show' to show details
type 'exit' to shutdown the server
""".format(__version__, __author__)

import os
import sys
import time
import threading
import socket
import select
import json

import paramiko

from ConfigParser import SafeConfigParser

from MiGBox.sftp.stub_sftp import StubServer, StubSFTPServer
from MiGBox.sync.delta import blockchksums, delta, patch
from MiGBox.sftp.sftp_common import CMD_BLOCKCHK, CMD_DELTA, CMD_PATCH 
from MiGBox.common import config_path, log_path, ABOUT

class SFTPServer(paramiko.SFTPServer):
    """
    This class inherits from L{paramiko.SFTPServer}.

    It is required here to overwrite/extend the paramiko.SFTPServer. 
    """

    def _process(self, t, request_number, msg):
        """
        Overwritten method for processing incoming requests to except
        and execute synchronization specific requests.

        This is a hook into the paramiko.SFTPServer implementation

        See L{paramiko.SFTPServer._process}
        """
        if t == CMD_BLOCKCHK:
            path = msg.get_string()
            bs = blockchksums(self.server._realpath(path))
            j = json.dumps(bs)
            message = paramiko.Message()
            message.add_int(request_number)
            message.add_string(j)
            self._send_packet(t, str(message))
            return
        elif t == CMD_DELTA:
            path = msg.get_string()
            bs = json.loads(msg.get_string())
            d = delta(self.server._realpath(path), bs)
            j = json.dumps(d)
            message = paramiko.Message()
            message.add_int(request_number)
            message.add_string(j)
            self._send_packet(t, str(message))
        elif t == CMD_PATCH:
            path = msg.get_string()
            d = json.loads(msg.get_string())
            patch(self.server._realpath(path), d)
            self._send_status(request_number, self.server.rename(path + ".patched", path))
        else:
            return paramiko.SFTPServer._process(self, t, request_number, msg)

class SFTPHandle(threading.Thread):
    def __init__(self, connection, address, userkey, hostkey, rootpath):
        super(SFTPHandle, self).__init__()
        self.conn = connection
        self.addr = address
        self.prvkey = hostkey
        self.usrkey = userkey
        self.rootpath = rootpath

    def run(self):
        self.transport = paramiko.Transport(self.conn)

        self.transport.add_server_key(paramiko.RSAKey.from_private_key_file(self.prvkey))

        event = threading.Event()

        server = StubServer(self.usrkey, self.rootpath)

	self.transport.set_subsystem_handler('sftp', SFTPServer, StubSFTPServer)

        self.transport.start_server(event, server)

        while self.transport.is_active():
            time.sleep(1)

        self.transport.close()
       
def main():
    """
    Main entry point to run the sftp server.
    """
    config = SafeConfigParser()
    config.read(os.path.join(config_path, 'server.cfg'))

    host = config.get('Connection', 'sftp_host')
    port = config.getint('Connection', 'sftp_port')
    backlog = config.getint('Connection', 'sftp_backlog')

    prvkey = config.get('KeyAuth', 'prvkey')
    usrkey = config.get('KeyAuth', 'usrkey')

    root_path = config.get('ROOT', 'root_path')

    log_file = config.get('Logging', 'log_file')
    log_level = config.get('Logging', 'log_level')

    paramiko.util.log_to_file(log_file, log_level)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    server_socket.bind((host,port))
    server_socket.listen(backlog)
    server_socket.setblocking(0)

    client_threads = []
    input_select = [server_socket, sys.stdin]

    print HEADER

    running = True
    while running:
        input_ready, output_ready, except_ready = select.select(input_select, [], [])

        for input_ in input_ready:
            if input_ == server_socket:
                conn, addr = server_socket.accept()
                thread = SFTPHandle(conn, addr, usrkey, prvkey, root_path)
                client_threads.append(thread)
                thread.start()
            elif input_ == sys.stdin:
                in_ = sys.stdin.readline()
                if in_.rstrip() == 'show':
                    print ABOUT
                if in_.rstrip() == 'exit':
                    running = False

    print 'Server is going down ...'

    for t in client_threads:
        t.transport.close()

    server_socket.close()

    print 'Done'

    sys.exit(0)

if __name__ == '__main__':
    main()
