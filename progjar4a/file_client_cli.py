import socket
import json
import base64
import logging
import time
import os
import csv

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

logging.basicConfig(level=logging.WARNING)
server_address = ('127.0.0.1', 6661)  # port server

def send_command(command_str=""):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    if not command_str.endswith("\r\n\r\n"):
        command_str += "\r\n\r\n"
    try:
        sock.sendall(command_str.encode())
        data_received = ""
        while True:
            data = sock.recv(52428800)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break
        return json.loads(data_received.strip())
    except Exception as e:
        logging.warning(f"Gagal kirim perintah: {e}")
        return False
    finally:
        sock.close()

def convert_file(filepath):
    with open(filepath, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode()
    return encoded_string

def remote_upload(filepath=""):
    filecontent = convert_file(filepath)
    command_str = f"UPLOAD {os.path.basename(filepath)} {filecontent}"
    hasil = send_command(command_str)
    if hasil and hasil.get('status') == 'OK':
        print(f"File {filepath} berhasil diupload")
        return True
    else:
        print(f"Gagal upload {filepath}")
        return False

def remote_download(filename):
    command_str = f"GET {filename}"
    hasil = send_command(command_str)
    
    if hasil:
        if hasil.get("status") == "OK":
            try:
                decoded_data = base64.b64decode(hasil.get('data_file', ''))
                output_filename = f"download_{filename}"
                with open(output_filename, "wb") as f:
                    f.write(decoded_data)
                print(f"Berhasil download: {output_filename}")
                return True
            except Exception as e:
                print(f"Gagal menyimpan file: {e}")
        else:
            print(f"Server error: {hasil.get('message')}")
    else:
        print("Gagal mendapatkan respon dari server.")
    return False

def stress_test(ukuran=10, jumlah_worker=5, operation='upload', mode='thread'):
    file_path = f"file_{ukuran}mb.bin"
    filename = os.path.basename(file_path)

    if not os.path.exists(file_path):
        print(f"File tidak ditemukan: {file_path}")
        return {
            'ukuran': ukuran,
            'worker': jumlah_worker,
            'op': operation,
            'pool': mode,
            'time': 0.0,
            'throughput': 0.0,
            'sukses': 0,
            'gagal': jumlah_worker
        }

    if operation == 'download':
        print(f"Memastikan file {file_path} sudah ada di server...")
        if not remote_upload(file_path):
            print("Gagal upload file sebelum proses download.")
            return {
                'ukuran': ukuran,
                'worker': jumlah_worker,
                'op': operation,
                'pool': mode,
                'time': 0.0,
                'throughput': 0.0,
                'sukses': 0,
                'gagal': jumlah_worker
            }

    total_size = os.path.getsize(file_path) if operation == 'upload' else (ukuran * 1024 * 1024)

    sukses = 0
    gagal = 0
    start_time = time.time()

    # Batasi max_workers proses biar gak terlalu berat
    if mode == 'process' and jumlah_worker > 10:
        print("Warning: Mengurangi jumlah worker proses ke 10 untuk menghindari OOM")
        jumlah_worker = 10

    executor_cls = ThreadPoolExecutor if mode == 'thread' else ProcessPoolExecutor
    futures = []
    with executor_cls(max_workers=jumlah_worker) as executor:
        for _ in range(jumlah_worker):
            if operation == 'upload':
                futures.append(executor.submit(remote_upload, file_path))
            else:
                futures.append(executor.submit(remote_download, filename))

        for future in as_completed(futures):
            try:
                if future.result():
                    sukses += 1
                else:
                    gagal += 1
            except Exception as e:
                print(f"Worker error: {e}")
                gagal += 1

    end_time = time.time()
    total_time = end_time - start_time
    throughput = (total_size * sukses / total_time) if total_time > 0 else 0.0

    return {
        'ukuran': ukuran,
        'worker': jumlah_worker,
        'op': operation,
        'pool': mode,
        'time': round(total_time, 2),
        'throughput': round(throughput, 2),
        'sukses': sukses,
        'gagal': gagal
    }

if __name__ == '__main__':
    ukuran_list = [10, 50, 100]
    client_worker_list = [1, 5, 10]  # Kurangi 50 jadi 10 untuk aman
    operasi_list = ['upload', 'download']
    pool_list = ['thread', 'process']
    server_worker_list = [1, 5, 10]  # Kurangi 50 jadi 10

    nomor = 1

    with open('rekap_stress_test.csv', 'w', newline='') as csvfile:
        fieldnames = [
            'Nomor', 'Operasi', 'Volume', 'Jumlah client worker pool', 'Jumlah server worker pool',
            'Waktu total per client', 'Throughput per client',
            'Jumlah worker client sukses', 'Jumlah worker client gagal',
            'Jumlah worker server sukses', 'Jumlah worker server gagal'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for ukuran in ukuran_list:
            for client_worker in client_worker_list:
                for operasi in operasi_list:
                    for pool in pool_list:
                        for server_worker in server_worker_list:
                            print(f"Running: {operasi.upper()} {ukuran}MB with {client_worker} client workers ({pool}) and {server_worker} server workers")

                            hasil = stress_test(ukuran, client_worker, operasi, pool)

                            if operasi == 'download' and hasil['throughput'] == 0.0 and hasil['time'] > 0:
                                hasil['throughput'] = (ukuran * 1024 * 1024 * hasil['sukses'] / hasil['time'])

                            sukses_server = 0
                            gagal_server = 0

                            writer.writerow({
                                'Nomor': nomor,
                                'Operasi': operasi,
                                'Volume': ukuran,
                                'Jumlah client worker pool': client_worker,
                                'Jumlah server worker pool': server_worker,
                                'Waktu total per client': hasil['time'],
                                'Throughput per client': round(hasil['throughput'], 2),
                                'Jumlah worker client sukses': hasil['sukses'],
                                'Jumlah worker client gagal': hasil['gagal'],
                                'Jumlah worker server sukses': sukses_server,
                                'Jumlah worker server gagal': gagal_server
                            })
                            csvfile.flush()  # Pastikan data langsung tertulis ke file
                            nomor += 1

                            print(f"→ Done: {hasil}")
