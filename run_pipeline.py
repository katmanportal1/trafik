"""
Katman Portal - Full Pipeline Runner
Crawl -> GA4 Data -> Dashboard -> docs/ -> Git Push

Kullanim:
  python run_pipeline.py              # Tum adimlar (akilli atlama aktif)
  python run_pipeline.py --force      # Her seyi zorla calistir
  python run_pipeline.py --no-push    # Git push yapma
"""
import subprocess
import sys
import shutil
import os
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
DASHBOARD_DIR = PROJECT_DIR / "dashboard"
DOCS_DIR = PROJECT_DIR / "docs"
CRAWLED_DIR = PROJECT_DIR / "Crawled_Data"
CACHE_DIR = PROJECT_DIR / "data_cache"

STALE_HOURS = 5  # Bu sureden eski veri yeniden indirilir


def is_fresh(directory, hours=STALE_HOURS):
    """Dizindeki en yeni dosya son N saat icinde mi?"""
    path = Path(directory)
    if not path.exists():
        return False
    newest = None
    for f in path.iterdir():
        if f.is_file():
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if newest is None or mtime > newest:
                newest = mtime
    if newest is None:
        return False
    age = datetime.now() - newest
    return age < timedelta(hours=hours)


def run_step(name, cmd):
    print(f"\n{'='*60}", flush=True)
    print(f"  [{datetime.now().strftime('%H:%M:%S')}] {name}", flush=True)
    print(f"{'='*60}", flush=True)
    result = subprocess.run(
        [sys.executable, cmd],
        cwd=PROJECT_DIR,
        timeout=600,
    )
    if result.returncode != 0:
        print(f"\n  HATA: {name} basarisiz (exit code {result.returncode})", flush=True)
        sys.exit(1)
    print(f"  [{datetime.now().strftime('%H:%M:%S')}] {name} - tamam", flush=True)


def copy_to_docs():
    print(f"\n{'='*60}", flush=True)
    print(f"  [{datetime.now().strftime('%H:%M:%S')}] Dashboard -> docs/ kopyalama", flush=True)
    print(f"{'='*60}", flush=True)

    if not DASHBOARD_DIR.exists():
        print("  HATA: dashboard/ klasoru bulunamadi", flush=True)
        sys.exit(1)

    DOCS_DIR.mkdir(exist_ok=True)
    count = 0
    for f in DASHBOARD_DIR.glob("*.html"):
        shutil.copy2(f, DOCS_DIR / f.name)
        count += 1
    print(f"  {count} dosya kopyalandi", flush=True)


def git_push():
    print(f"\n{'='*60}", flush=True)
    print(f"  [{datetime.now().strftime('%H:%M:%S')}] Git commit & push", flush=True)
    print(f"{'='*60}", flush=True)

    os.chdir(PROJECT_DIR)
    today = datetime.now().strftime("%Y-%m-%d")

    subprocess.run(["git", "add", "docs/"], check=True)

    result = subprocess.run(["git", "diff", "--cached", "--quiet", "docs/"])
    if result.returncode == 0:
        print("  Degisiklik yok, commit atlaniyor", flush=True)
        return

    msg = f"Update dashboards for {today}"
    subprocess.run(["git", "commit", "-m", msg], check=True)
    subprocess.run(["git", "push"], check=True)
    print(f"  Push tamam: {msg}", flush=True)


def main():
    args = sys.argv[1:]
    force = "--force" in args
    skip_push = "--no-push" in args

    start = datetime.now()
    print(f"\nKATMAN PORTAL PIPELINE - {start.strftime('%Y-%m-%d %H:%M')}", flush=True)
    print(f"  Kural: {STALE_HOURS} saatten yeni veri varsa adim atlanir", flush=True)

    # Adim 1: Crawl
    if force or not is_fresh(CRAWLED_DIR):
        run_step("Adim 1: Website tarama", "katman_full_crawler.py")
    else:
        print(f"\n  [ATLANDI] Crawl (son {STALE_HOURS} saat icinde taranmis)", flush=True)

    # Adim 2: GA4 veri cekme
    if force or not is_fresh(CACHE_DIR):
        run_step("Adim 2: GA4 veri cekme", "analytics_helper.py")
    else:
        print(f"\n  [ATLANDI] GA4 fetch (son {STALE_HOURS} saat icinde cekilmis)", flush=True)

    # Adim 3: Dashboard olusturma (her zaman calisir)
    run_step("Adim 3: Dashboard olusturma", "generate_report.py")

    # Adim 4: docs/ kopyalama
    copy_to_docs()

    # Adim 5: Git push
    if not skip_push:
        git_push()
    else:
        print("\n  [ATLANDI] Git push (--no-push)", flush=True)

    elapsed = datetime.now() - start
    print(f"\n{'='*60}", flush=True)
    print(f"  PIPELINE TAMAM - {elapsed.total_seconds():.0f} saniye", flush=True)
    print(f"{'='*60}\n", flush=True)


if __name__ == "__main__":
    main()
