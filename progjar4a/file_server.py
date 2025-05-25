import socket
import threading
import logging
import os
import base64
import json

SERVER_PORT = 6661
FILES_DIR = "server_files"

if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

def handle_client(conn, addr):
    try:
        data_received = ""
        while True:
            data = conn.recv(52428800)
            if not data:
                break
            data_received += data.decode()
            if "\r\n\r\n" in data_received:
                break

        cmd = data_received.strip().split()
        if not cmd:
            response = json.dumps({"status": "ERROR", "message": "Command kosong"})
        elif cmd[0] == "LIST":
            files = os.listdir(FILES_DIR)
            response = json.dumps({"status": "OK", "data": files})

        elif cmd[0] == "GET":
            if len(cmd) < 2:
                response = json.dumps({"status": "ERROR", "message": "GET butuh nama file"})
            else:
                filename = cmd[1]
                filepath = os.path.join(FILES_DIR, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        encoded = base64.b64encode(f.read()).decode()
                    response = json.dumps({"status": "OK", "data_namafile": filename, "data_file": encoded})
                else:
                    response = json.dumps({"status": "ERROR", "message": "File tidak ditemukan"})

        elif cmd[0] == "UPLOAD":
            if len(cmd) < 3:
                response = json.dumps({"status": "ERROR", "message": "UPLOAD butuh nama file dan data"})
            else:
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
    logging.warning(f"Server listening on port {SERVER_PORT}")

    while True:
        conn, addr = s.accept()
        logging.warning(f"Connection from {addr}")
        t = threading.Thread(target=handle_client, args=(conn, addr))
        t.start()

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    run_server()
