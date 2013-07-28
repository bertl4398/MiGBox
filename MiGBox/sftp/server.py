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
import base64

import paramiko

from MiGBox.sync.delta import blockchecksums, delta, patch
from MiGBox.sftp.common  import CMD_BLOCKCHK, CMD_DELTA, CMD_PATCH 
from MiGBox.common import ABOUT
from MiGBox.sftp.server_interface import SFTPServerInterface

class Server(paramiko.ServerInterface):
    """
    This class inherits from L{paramiko.SFTPServer}.

    It handles the public key authentication.
    """

    def __init__(self, root, userkey):
        """
        Create a new server that handles the public key authentication.

        @param root: root path of the server.
        @type root: str
        @param userkey: path to the user's public key.
        @type userkey: str
        """

        super(Server, self).__init__()
        self.root = root
        self.userkey = userkey

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED

    def check_auth_publickey(self, username, key):
        with open(self.userkey, 'rb') as f:
            key_data = f.read()
        # file format "ssh-rsa AAA.... user@somemachine" 
        key_data = key_data.split(' ')[1]
        rsakey = paramiko.RSAKey(data=base64.decodestring(key_data))
        if key == rsakey:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'publickey'

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
            bs = blockchecksums(self.server._get_path(path))
            j = json.dumps(bs)
            message = paramiko.Message()
            message.add_int(request_number)
            message.add_string(j)
            self._send_packet(t, str(message))
            return
        elif t == CMD_DELTA:
            path = msg.get_string()
            bs = json.loads(msg.get_string())
            d = delta(self.server._get_path(path), bs)
            j = json.dumps(d)
            message = paramiko.Message()
            message.add_int(request_number)
            message.add_string(j)
            self._send_packet(t, str(message))
        elif t == CMD_PATCH:
            path = msg.get_string()
            d = json.loads(msg.get_string())
            patched = patch(self.server._get_path(path), d)
            self._send_status(request_number, self.server.rename(patched, path))
        else:
            return paramiko.SFTPServer._process(self, t, request_number, msg)

    def run_server(cls, conn, addr, hostkey, userkey, root):
        transport = paramiko.Transport(conn)
        transport.add_server_key(paramiko.RSAKey.from_private_key_file(hostkey))
        transport.set_subsystem_handler('sftp', cls, SFTPServerInterface)
        transport.start_server(threading.Event(), Server(root, userkey))

        while transport.is_active():
            time.sleep(1)

        transport.close()

    run_server = classmethod(run_server)

def main(host, port, backlog, prvkey, usrkey, root_path, log_file, log_level):
    """
    Main entry point to run the sftp server.
    """

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
                thread = threading.Thread(target=SFTPServer.run_server,
                                          args=(conn, addr, prvkey, usrkey, root_path))
                client_threads.append(thread)
                thread.start()
            elif input_ == sys.stdin:
                in_ = sys.stdin.readline()
                if in_.rstrip() == 'show':
                    print ABOUT
                if in_.rstrip() == 'exit':
                    running = False

    print 'Server is going down ...'

    server_socket.close()

    print 'Done'

    sys.exit(0)

if __name__ == '__main__':
    host = '' 
    port = 50007 
    backlog = 10 

    prvkey = '/home/benjamin/MiGBox/keys/server_rsa_key'
    usrkey = '/home/benjamin/MiGBox/keys/user_rsa_key.pub'

    root_path = '/home/benjamin/MiGBox/MiGBox/sftp'

    log_file = '/home/benjamin/MiGBox/MiGBox/sftp/log'
    log_level = 'INFO' 

    main(host, port, backlog, prvkey, usrkey, root_path, log_file, log_level)
