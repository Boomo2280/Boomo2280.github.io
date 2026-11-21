#!/usr/bin/env python3
"""Проверяет, какие погодные сервисы открываются с ЭТОГО компьютера без VPN.
Запуск:  python weather_check.py
Ответ с ошибкой 401/403 тоже считается «доступен»: сервер ответил, просто нужен ключ."""
import time
import urllib.error
import urllib.request

LAT, LON = 67.61, 33.66
SERVICES = [
    ("Open-Meteo",        f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m"),
    ("MET Norway",        f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={LAT}&lon={LON}"),
    ("wttr.in",           f"https://wttr.in/Kirovsk?format=j1"),
    ("7timer",            f"https://www.7timer.info/bin/api.pl?lon={LON}&lat={LAT}&product=civillight&output=json"),
    ("OpenWeatherMap",    f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}"),
    ("Яндекс Погода",     f"https://api.weather.yandex.ru/v2/forecast?lat={LAT}&lon={LON}"),
    ("Gismeteo",          "https://api.gismeteo.net/v2/weather/current/"),
    ("WeatherAPI",        "https://api.weatherapi.com/v1/current.json?q=Kirovsk"),
]

for name, url in SERVICES:
    t = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": "portal-weather-check/1.0 (student project)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            status = f"OK ({r.status}), данные получены"
    except urllib.error.HTTPError as e:
        status = f"доступен (ответ {e.code}; для работы нужен ключ)" if e.code in (400, 401, 403) else f"ответил с ошибкой {e.code}"
    except Exception as e:
        status = f"НЕ ОТКРЫВАЕТСЯ ({type(e).__name__})"
    print(f"{name:16} {time.time() - t:5.1f} c  {status}")
