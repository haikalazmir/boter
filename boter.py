import time
import subprocess
import json
import shutil
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
    except json.JSONDecodeError as e:
        print(f"Format file {config_path} tidak valid: {e}")
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

def get_executable(command):
    """Mendeteksi Python/Node.js di sistem."""
    executable = shutil.which(command)
    if not executable:
        # Jika Python3 tidak ditemukan, coba Python
        if command == 'python3':
            executable = shutil.which('python')  # Fallback ke python
        elif command == 'node':
            executable = shutil.which('node')  # Fallback ke node.js
    if not executable:
        print(f"{command.capitalize()} tidak ditemukan. Pastikan {command} sudah diinstal.")
        exit(1)
    return executable

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
    """Menjalankan skrip bot berdasarkan jenis yang dipilih."""
    global current_process
    try:
        # Tentukan perintah berdasarkan jenis bot
        if config["bot_type"] == "python":
            command = [get_executable('python3'), config["script_path"]]
        elif config["bot_type"] == "node":
            command = [get_executable('node'), config["script_path"]]
        else:
            print(f"Jenis bot tidak didukung: {config['bot_type']}")
            return

        # Jalankan proses bot
        current_process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            text=True
        )

        # Jeda sebelum menjawab pertanyaan
        print("Menunggu bot siap menerima input...")
        time.sleep(2)

        # Mengirimkan jawaban otomatis ke bot dengan jeda di antaranya
        for input_data in config["inputs"]:
            current_process.stdin.write(input_data)
            current_process.stdin.flush()
            print(f"Jawaban dikirim: {input_data.strip()}")
            time.sleep(1)

        current_process.stdin.close()  # Tutup input setelah selesai menulis
        print("Skrip bot berhasil dijalankan.")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

def start_monitoring():
    """Mulai memantau folder."""
    event_handler = FolderWatcher()
    observer = Observer()
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
