import PyInstaller.__main__
import os
import sys
import shutil
import time

# Konfigurasi Utama
SCRIPT_NAME = "spy_bot.py"
EXE_NAME = "WindowsHealthMonitor"  # Nama EXE hasil akhir
ICON_FILE = "shield.ico"
VERSION_FILE = "version_info.txt"
RESULT_FOLDER = "Hasil Bot"

# File tambahan yang WAJIB masuk ke dalam EXE
ASSETS = [
    "alarm.wav",
    "joko.wav",
    "banner.png"
]

# Library yang sering "ketinggalan" oleh PyInstaller
HIDDEN_IMPORTS = [
    "pycaw",
    "comtypes",
    "pynput.keyboard._win32",
    "pynput.mouse._win32",
    "cv2",
    "pyautogui"
]

def build():
    print(f"--- MEMULAI PROSES BUILD: {EXE_NAME} ---")
    
    # 1. Bersihkan folder lama agar tidak bentrok
    folders_to_clean = ["build", "dist", RESULT_FOLDER]
    for folder in folders_to_clean:
        if os.path.exists(folder):
            print(f"🧹 Membersihkan {folder}...")
            shutil.rmtree(folder)

    # 2. Pastikan file script utama ada
    if not os.path.exists(SCRIPT_NAME):
        print(f"❌ ERROR: File {SCRIPT_NAME} tidak ditemukan!")
        return

    # 3. Siapkan parameter dasar
    params = [
        SCRIPT_NAME,
        '--noconfirm',
        '--onefile',      # Jadikan satu file tunggal
        '--windowed',     # Tanpa muncul layar hitam CMD
        f'--name={EXE_NAME}',
    ]

    # 4. Tambahkan Icon jika ada
    if os.path.exists(ICON_FILE):
        params.append(f'--icon={ICON_FILE}')
    
    # 5. Tambahkan Version Info jika ada
    if os.path.exists(VERSION_FILE):
        params.append(f'--version-file={VERSION_FILE}')

    # 6. Masukkan aset (audio/gambar)
    for asset in ASSETS:
        if os.path.exists(asset):
            # Format: 'file_asal;tujuan_di_dalam_exe' (titik berarti root)
            params.append(f'--add-data={asset}{os.pathsep}.')
            print(f"✅ Aset ditambahkan: {asset}")
        else:
            print(f"⚠️ Warning: Aset {asset} tidak ditemukan, EXE mungkin error saat fitur tersebut dipanggil.")

    # 7. Tambahkan Hidden Imports
    for imp in HIDDEN_IMPORTS:
        params.append(f'--hidden-import={imp}')

    # 8. Eksekusi PyInstaller
    print("\n📦 Sedang membungkus... (Ini butuh waktu 1-3 menit)\n")
    try:
        PyInstaller.__main__.run(params)
        
        # 9. Finishing Touches: Rename & Clean Build
        # Beri jeda sebentar agar OS melepas kunci folder (mencegah Access Denied)
        time.sleep(3)
        
        if os.path.exists("dist"):
            # Coba rename dengan retry logic
            for i in range(5):
                try:
                    if os.path.exists(RESULT_FOLDER):
                        shutil.rmtree(RESULT_FOLDER)
                    os.rename("dist", RESULT_FOLDER)
                    print(f"📂 Folder 'dist' berhasil di-rename menjadi '{RESULT_FOLDER}'")
                    break
                except Exception as e:
                    if i == 4: raise e
                    print(f"⚠️ Percobaan {i+1} gagal memindahkan folder, mencoba lagi...")
                    time.sleep(2)
        
        if os.path.exists("build"):
            shutil.rmtree("build")
            print("🧹 Folder 'build' telah dihapus.")
            
        spec_file = f"{EXE_NAME}.spec"
        if os.path.exists(spec_file):
            os.remove(spec_file)
            print(f"🧹 File spec {spec_file} telah dibersihkan.")

        print("\n" + "="*30)
        print(f"✨ BUILD BERHASIL SEMPURNA! ✨")
        print(f"Silahkan cek folder '{RESULT_FOLDER}' untuk mengambil file: {EXE_NAME}.exe")
        print("="*30)
    except Exception as e:
        print(f"❌ Gagal saat proses build: {e}")

if __name__ == "__main__":
    build()
