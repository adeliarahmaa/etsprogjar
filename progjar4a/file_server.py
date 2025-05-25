from socket import *
import socket
import threading
import logging
import time
import sys
from concurrent.futures import ThreadPoolExecutor


from file_protocol import  FileProtocol
fp = FileProtocol()


class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        buffer = b""
        while True:
            data = self.connection.recv(4096)
            if not data:
                break
            buffer += data
            # Cek dua kemungkinan delimiter
            while b"\r\n\r\n" in buffer or b"\n\n" in buffer:
                if b"\r\n\r\n" in buffer:
                    delimiter = b"\r\n\r\n"
                else:
                    delimiter = b"\n\n"
                parts = buffer.split(delimiter, 1)
                d = parts[0].decode()
                hasil = fp.proses_string(d)
                hasil = hasil + "\r\n\r\n"
                self.connection.sendall(hasil.encode())
                buffer = parts[1]
        self.connection.close()


class Server(threading.Thread):
    def __init__(self,ipaddress='0.0.0.0',port=8889):
        self.ipinfo=(ipaddress,port)
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

    def run(self):
        logging.warning(f"server berjalan di ip address {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(1)
        with ThreadPoolExecutor(max_workers=1) as executor:
            while True:
                self.connection, self.client_address = self.my_socket.accept()
                logging.warning(f"connection from {self.client_address}")

                executor.submit(ProcessTheClient(self.connection, self.client_address).run)
                self.the_clients.append(self.connection)


def main():
    svr = Server(ipaddress='0.0.0.0',port=6666)
    svr.start()
    svr.join()


if __name__ == "__main__":
    main()

