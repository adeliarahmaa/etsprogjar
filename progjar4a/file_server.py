# stress_test_server.py
import socket
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import logging
import os
import base64
import json

MODE = "thread"  # atau "process"
WORKER_COUNT = 5
SERVER_PORT = 6666
FILES_DIR = "server_files"

if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

def handle_client(conn, addr):
    try:
        data_received = ""
        while True:
            data = conn.recv(1024)
            if not data:
                break
            data_received += data.decode()
            if "\r\n\r\n" in data_received:
                break

        cmd = data_received.strip().split()
        if cmd[0] == "LIST":
            files = os.listdir(FILES_DIR)
            response = json.dumps({"status": "OK", "data": files})

        elif cmd[0] == "GET":
            filename = cmd[1]
            filepath = os.path.join(FILES_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    encoded = base64.b64encode(f.read()).decode()
                response = json.dumps({"status": "OK", "data_namafile": filename, "data_file": encoded})
            else:
                response = json.dumps({"status": "ERROR", "message": "File not found"})

        elif cmd[0] == "UPLOAD":
            filename = cmd[1]
            encoded_data = cmd[2]
            with open(os.path.join(FILES_DIR, filename), 'wb') as f:
                f.write(base64.b64decode(encoded_data))
            response = json.dumps({"status": "OK", "message": "Upload sukses"})

        else:
            response = json.dumps({"status": "ERROR", "message": "Command tidak dikenali"})

        conn.sendall((response + "\r\n\r\n").encode())

    except Exception as e:
        logging.warning(f"Error handling client {addr}: {e}")
    finally:
        conn.close()

def run_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', SERVER_PORT))
    s.listen(100)
    logging.warning(f"Server listening on port {SERVER_PORT} with {WORKER_COUNT} {MODE} workers")

    if MODE == "thread":
        pool = ThreadPoolExecutor(max_workers=WORKER_COUNT)
    else:
        pool = ProcessPoolExecutor(max_workers=WORKER_COUNT)

    while True:
        conn, addr = s.accept()
        pool.submit(handle_client, conn, addr)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    run_server()
