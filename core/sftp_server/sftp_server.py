#!/usr/bin/python
#
# SFTP server based on paramiko
#
# Copyright (C) 2013 Benjamin Ertl

"""
SFTP server implementation based on paramiko.
"""

__version__ = 0.2
__author__ = 'Benjamin Ertl'

import sys, time, threading, socket
import traceback
import ConfigParser

import paramiko

from stub_sftp import StubServer, StubSFTPServer

def main():
    config = ConfigParser.ConfigParser()
    config.read('server.cfg')

    host = config.get('Connection', 'host')
    port = int(config.get('Connection', 'port'))
    backlog = int(config.get('Connection', 'backlog'))

    log_level = config.get('Logging', 'level')
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

            t.set_subsystem_handler('sftp', paramiko.SFTPServer, StubSFTPServer)

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
