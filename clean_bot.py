import os
import subprocess
import winreg
import time

def clean_bot():
    print("🧹 Memulai proses pembersihan total...")

    # 1. Daftar proses yang mungkin sedang berjalan
    target_processes = ["WinHelper.exe", "ServiceTask.exe", "WindowsHealthMonitor.exe"]
    
    for proc in target_processes:
        try:
            print(f"🛑 Menghentikan proses: {proc}...")
            subprocess.run(["taskkill", "/F", "/IM", proc], capture_output=True)
        except: pass

    time.sleep(1)

    # 2. Daftar Registry yang harus dihapus
    startup_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_names = ["WindowsHealthMonitor", "WindowsMediaService"]

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_path, 0, winreg.KEY_SET_VALUE) as key:
            for app in app_names:
                try:
                    winreg.DeleteValue(key, app)
                    print(f"🗑️ Registry '{app}' berhasil dihapus.")
                except FileNotFoundError:
                    pass
    except Exception as e:
        print(f"⚠️ Gagal akses Registry: {e}")

    # 3. Daftar folder persembunyian
    paths_to_delete = [
        os.path.join(os.environ['APPDATA'], "WindowsHealth"),
        os.path.join(os.environ['LOCALAPPDATA'], "ServiceData"),
        os.path.join(os.environ['APPDATA'], "SystemLogs") # Folder Logs & Media
    ]

    for path in paths_to_delete:
        if os.path.exists(path):
            try:
                import shutil
                shutil.rmtree(path)
                print(f"✅ Folder berhasil dihapus: {path}")
            except Exception as e:
                print(f"❌ Gagal menghapus {path}: {e}")

    print("\n✨ SISTEM SEKARANG BERSIH TOTAL! ✨")
    print("Bot sudah tidak akan aktif lagi saat startup.")

if __name__ == "__main__":
    clean_bot()
    input("\nTekan Enter untuk menutup...")
