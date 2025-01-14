import socket

def check_port_used(port: int, ip='127.0.0.1'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_result = sock.connect_ex((ip, port))
    if sock_result == 0:
        return True
    return False

def save_file(filepath: str, content: str):
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content)
