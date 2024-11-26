import socket


class Socket:

    @staticmethod
    def check_port_used(port: int, ip='127.0.0.1'):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_result = sock.connect_ex((ip, port))
        if sock_result == 0:
            return True
        return False