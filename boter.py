import time
import os
import subprocess
import json
import sys  # Menambahkan import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Global variables untuk konfigurasi
config = {}

# Fungsi untuk membaca konfigurasi dari file settings.json
def load_config():
    global config
    config_path = 'settings.json'
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print("Konfigurasi berhasil dimuat.")
    except FileNotFoundError:
        print(f"File konfigurasi {config_path} tidak ditemukan. Pastikan file tersedia.")
        exit(1)
    except json.JSONDecodeError:
        print(f"Format file {config_path} tidak valid. Periksa isinya.")
        exit(1)

# Proses bot yang sedang berjalan
current_process = None

class FolderWatcher(FileSystemEventHandler):
    """Handler untuk memantau perubahan pada folder."""
    def on_modified(self, event):
        global current_process

        # Abaikan perubahan pada folder
        if event.is_directory:
            return

        # Cek perubahan pada file yang dipantau
        if event.src_path == config["data_file_path"]:
            print(f"Perubahan terdeteksi pada file: {event.src_path}")
            restart_bot()

def stop_bot():
    """Menghentikan proses bot jika masih aktif."""
    global current_process
    if current_process:
        if current_process.poll() is None:  # Proses masih berjalan
            print("Menghentikan bot...")
            current_process.terminate()
            try:
                current_process.wait(timeout=10)  # Tunggu hingga proses selesai
                print("Bot berhasil dihentikan.")
            except subprocess.TimeoutExpired:
                print("Proses tidak merespons. Memaksa penghentian...")
                current_process.kill()  # Paksa berhenti
                current_process.wait()
        else:
            print("Proses bot sudah berhenti.")
    else:
        print("Tidak ada proses bot yang berjalan.")

def restart_bot():
    """Menghentikan bot yang sedang berjalan dan memulai ulang setelah jeda."""
    print(f"Menunggu {config['restart_delay']} detik sebelum memulai ulang bot...")
    time.sleep(config['restart_delay'])
    stop_bot()
    print("Memulai ulang bot...")
    start_bot()

def start_bot():
    """Menjalankan skrip Python sebagai bot, mengirimkan input otomatis jika diatur."""
    global current_process
    try:
        # Menyesuaikan perintah berdasarkan OS
        python_command = "python3" if sys.platform != "win32" else "python"
        
        # Menjalankan main.py sebagai proses baru
        current_process = subprocess.Popen(
            [python_command, config["python_script_path"]],
            stdin=subprocess.PIPE,  # Mengatur stdin agar dapat mengirimkan input
            text=True  # Memastikan input dalam format teks (bukan byte)
        )

        # Jeda sebelum bot siap
        print("Menunggu bot siap menerima input...")
        time.sleep(2)  # Jeda awal agar bot siap

        # Pengecekan apakah input otomatis diaktifkan
        if config.get("send_auto_input", "no").lower() == "yes":
            # Mengirimkan jawaban otomatis ke bot dengan jeda di antaranya
            for input_data in config["inputs"]:
                current_process.stdin.write(input_data)  # Kirim input ke proses
                current_process.stdin.flush()  # Pastikan data langsung dikirimkan
                print(f"Jawaban dikirim: {input_data.strip()}")
                time.sleep(0.5)  # Jeda 0.5 detik di antara jawaban
        else:
            print("Input otomatis tidak dikirimkan berdasarkan pengaturan.")

        current_process.stdin.close()  # Tutup input setelah selesai menulis
        print("Skrip bot berhasil dijalankan.")
    except FileNotFoundError:
        print("Python3 tidak ditemukan. Pastikan Python3 sudah terinstal.")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

def start_monitoring():
    """Mulai memantau folder."""
    event_handler = FolderWatcher()
    observer = Observer()
    # Memantau folder berdasarkan konfigurasi
    observer.schedule(event_handler, path=config["monitoring_folder"], recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    # Memuat konfigurasi
    load_config()

    # Menjalankan skrip bot pertama kali saat skrip dimulai
    start_bot()
    start_monitoring()
