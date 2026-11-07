@echo off
cd /d "%~dp0"
python update.py
git add schedule.json schedule.png news.json
git commit -m "Автообновление данных"
git push
