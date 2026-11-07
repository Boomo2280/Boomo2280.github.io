@echo off
rem ===== SETTINGS: check both paths =====
set REPO=D:\OSPanel\domains\localhost\Github\Boomo2280.github.io
set PY=C:\Users\Boomo\AppData\Local\Python\pythoncore-3.14-64\python.exe
rem =========================================

cd /d "%REPO%" || exit /b 1
echo ===== %date% %time% ===== >> update.log

git pull --rebase --autostash >> update.log 2>&1
"%PY%" update.py >> update.log 2>&1

git add -- schedule.json news.json >> update.log 2>&1
if exist schedule.png git add -- schedule.png >> update.log 2>&1

git diff --cached --quiet && (echo no changes >> update.log & exit /b 0)
git commit -m "Auto update data" >> update.log 2>&1
git push >> update.log 2>&1
