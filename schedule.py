"""
Katman Portal - Windows Task Scheduler
Her 6 saatte run_pipeline.py calistirir (00:00, 06:00, 12:00, 18:00).

Kullanim:
    python schedule.py          # Gorevi olustur
    python schedule.py --remove # Gorevi kaldir
    python schedule.py --status # Gorev durumunu goster
"""
import subprocess
import sys
import os

TASK_NAME = "KatmanPortal_Pipeline"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(BASE_DIR, "run_pipeline.py")


def find_python():
    return sys.executable


def create_task():
    python_exe = find_python()

    # 6 saatte bir: /SC HOURLY /MO 6
    cmd = [
        "schtasks", "/Create",
        "/TN", TASK_NAME,
        "/TR", f'"{python_exe}" "{SCRIPT_PATH}"',
        "/SC", "HOURLY",
        "/MO", "6",
        "/F",
        "/RL", "HIGHEST",
    ]

    print(f"Gorev olusturuluyor: {TASK_NAME}", flush=True)
    print(f"  Python: {python_exe}", flush=True)
    print(f"  Script: {SCRIPT_PATH}", flush=True)
    print(f"  Zamanlama: Her 6 saatte bir", flush=True)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"\nBasarili! Gorev '{TASK_NAME}' olusturuldu.", flush=True)
    else:
        print(f"\nHATA: {result.stderr}", flush=True)
        print("Not: Yonetici (Administrator) olarak calistirmayi deneyin.", flush=True)


def remove_task():
    cmd = ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"Gorev '{TASK_NAME}' kaldirildi.", flush=True)
    else:
        print(f"HATA: {result.stderr}", flush=True)


def show_status():
    cmd = ["schtasks", "/Query", "/TN", TASK_NAME, "/V", "/FO", "LIST"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(result.stdout, flush=True)
    else:
        print(f"Gorev bulunamadi: {TASK_NAME}", flush=True)


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "--remove":
            remove_task()
        elif arg == "--status":
            show_status()
        else:
            print(f"Bilinmeyen arguman: {arg}", flush=True)
            print("Kullanim: python schedule.py [--remove | --status]", flush=True)
    else:
        create_task()


if __name__ == "__main__":
    main()
