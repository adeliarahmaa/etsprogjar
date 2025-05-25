import socket
import json
import base64
import logging
import time
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

# Setup logging
logging.basicConfig(level=logging.WARNING)

server_address = ('127.0.0.1', 6666)

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    if not command_str.endswith("\r\n\r\n"):
        command_str += "\r\n\r\n"
    try:
        sock.sendall(command_str.encode())
        data_received = ""
        while True:
            data = sock.recv(1024)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break
        return json.loads(data_received)
    except:
        return False

def convert_file(filepath):
    try:
        with open(filepath, 'rb') as f:
            encoded = base64.b64encode(f.read())
            return encoded.decode("utf-8")
    except Exception as e:
        print(f"Gagal konversi file: {e}")
        return False

def remote_upload(filepath):
    filecontent = convert_file(filepath)
    if not filecontent:
        return False
    command_str = f"UPLOAD {filepath} {filecontent}"
    hasil = send_command(command_str)
    return hasil and hasil.get("status") == "OK"

def remote_download(filename):
    command_str = f"GET {filename}"
    hasil = send_command(command_str)
    if hasil and hasil.get("status") == "OK":
        try:
            with open(f"download_{filename}", "wb") as f:
                f.write(base64.b64decode(hasil['data_file']))
            return True
        except Exception as e:
            print(f"Gagal menyimpan file: {e}")
            return False
    return False

def stress_test(operation='upload', file_path_or_name='file_10mb.dat', jumlah_worker=5, mode='thread'):
    sukses = 0
    gagal = 0
    total_size = os.path.getsize(file_path_or_name) if operation == 'upload' else 0
    start_time = time.time()

    executor_cls = ThreadPoolExecutor if mode == 'thread' else ProcessPoolExecutor
    futures = []
    with executor_cls(max_workers=jumlah_worker) as executor:
        for _ in range(jumlah_worker):
            if operation == 'upload':
                futures.append(executor.submit(remote_upload, file_path_or_name))
            else:
                futures.append(executor.submit(remote_download, file_path_or_name))

        for future in as_completed(futures):
            if future.result():
                sukses += 1
            else:
                gagal += 1

    end_time = time.time()
    total_time = end_time - start_time
    throughput = (total_size * sukses / total_time) if total_time > 0 else 0

    print(f"\n=== Stress Test Result ===")
    print(f"Operation       : {operation}")
    print(f"Mode            : {mode}")
    print(f"File            : {file_path_or_name}")
    print(f"Jumlah Worker   : {jumlah_worker}")
    print(f"Total Time      : {total_time:.2f} seconds")
    print(f"Throughput      : {throughput:.2f} bytes/sec")
    print(f"Success         : {sukses}")
    print(f"Failed          : {gagal}")
    print("==========================\n")

# Contoh penggunaan langsung
if __name__ == '__main__':
    server_address = ('127.0.0.1', 6666)  # alamat server kamu
    kombinasi = []
    ukuran_list = [10, 50, 100]
    worker_list = [1, 5, 50]
    operasi_list = ['upload', 'download']
    pool_list = ['thread', 'process']

    with open('hasil_stress_test.csv', 'w', newline='') as csvfile:
        fieldnames = ['ukuran', 'worker', 'op', 'pool', 'time', 'throughput', 'sukses', 'gagal']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for ukuran in ukuran_list:
            for worker in worker_list:
                for operasi in operasi_list:
                    for pool in pool_list:
                        print(f"Running: {operasi.upper()} {ukuran}MB with {worker} worker ({pool})")
                        hasil = jalankan_stress_test(ukuran, worker, operasi, pool)
                        writer.writerow(hasil)
                        print(f"→ Done: {hasil}")

