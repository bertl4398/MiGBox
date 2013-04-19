"""
SFTP server based on paramiko.
"""

import socket, time

try:
    import paramiko
except ImportError:
    print 'Install python paramiko module first'

from stub_sftp import StubServer, StubSFTPServer

SFTP_PORT = 8888 # port for the sftp server to listen
BACKLOG = 10 # number of connection tries to buffer

LEVEL = 'INFO' # paramiko log level

paramiko_log_level = getattr(paramiko.common, LEVEL)
paramiko.common.logging.basicConfig(level=paramiko_log_level)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

server_socket.bind(('', SFTP_PORT))
server_socket.listen(BACKLOG)

def run():
    try:
        while True:
            conn, addr = server_socket.accept()
            host_key = paramiko.RSAKey.from_private_key_file('test_rsa.key')
            transport = paramiko.Transport(conn)
            transport.add_server_key(host_key)
            transport.set_subsystem_handler('sftp', paramiko.SFTPServer, \
                                            StubSFTPServer)
            server = StubServer()
            transport.start_server(server=server)
            channel = transport.accept()

            while transport.is_active():
                time.sleep(1)
    finally:
        server_socket.close()

if __name__ == '__main__':
    run()

