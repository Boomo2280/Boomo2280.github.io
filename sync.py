#!/usr/bin/env python3
"""Один скрипт: подтянуть репозиторий -> обновить данные -> отправить на GitHub.

Запуск вручную:       python sync.py
Планировщик Windows:  программа  python.exe   аргументы  sync.py   рабочая папка  = папка репозитория
Лог пишется в update.log рядом со скриптом.
"""
import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import update   # update.py должен лежать рядом

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "update.log"
# что отправляем на GitHub (отсутствующие файлы пропускаются)
FILES = ["schedule.json", "schedule.png", "news.json", "news_img"]


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def find_git():
    """Ищет git.exe: сначала в PATH, затем в обычных местах установки Windows."""
    found = shutil.which("git")
    if found:
        return found
    local = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        os.path.join(local, r"Programs\Git\cmd\git.exe"),
        *sorted(glob.glob(os.path.join(local, r"GitHubDesktop\app-*\resources\app\git\cmd\git.exe")), reverse=True),
    ]
    return next((c for c in candidates if os.path.exists(c)), None)


GIT = find_git()


def git(*args):
    r = subprocess.run([GIT, *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout + r.stderr).strip()
    if out:
        log(f"git {' '.join(args)}: {out}")
    return r.returncode


def main():
    log("=== запуск ===")
    if GIT:
        log(f"git: {GIT}")
        git("pull", "--rebase", "--autostash")
    else:
        log("git не найден: данные обновятся, но на GitHub отправлены не будут "
            "(установите Git for Windows: https://git-scm.com/download/win)")

    fails = update.run(ROOT)
    if fails:
        log(f"обновление прошло с ошибками (частей с ошибкой: {fails}); отправляю то, что получилось")

    if not GIT:
        return 1
    for f in FILES:
        if (ROOT / f).exists():
            git("add", "-A", "--", f)
    # ничего не изменилось -> выходим
    if git("diff", "--cached", "--quiet") == 0:
        log("изменений нет, отправлять нечего")
        return 0

    if git("commit", "-m", f"Автообновление данных {datetime.now():%d.%m.%Y %H:%M}") != 0:
        log("не удалось создать коммит")
        return 1
    if git("push") != 0:
        log("push отклонён, пробую подтянуть изменения и повторить")
        git("pull", "--rebase", "--autostash")
        if git("push") != 0:
            log("НЕ УДАЛОСЬ отправить на GitHub (проверьте вход в git)")
            return 1
    log("готово: данные отправлены на GitHub")
    return 0


if __name__ == "__main__":
    sys.exit(main())
