#!/usr/bin/env python3
"""Обновляет schedule.json и news.json для студенческого портала.

Запуск:  python update.py            (файлы пишутся рядом со скриптом)
         python update.py --out data (писать в папку data)
         python update.py --debug    (показать, что скрипт видит в PDF и на сайте)
"""
import argparse, json, re, sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests

# ===================== НАСТРОЙКИ =====================
BASE = "https://kf.mauniver.ru/"
GROUP = "1-ТЭСИС"                              # только для сообщений; поиск идёт по header_template.png
PDF_URL = BASE + "raspisanie/{d}_s.pdf"      # {d} -> 09.11.2026
NEWS_LIMIT = 8
TZ = ZoneInfo("Europe/Moscow")
IMAGE_NAME = "schedule.png"      # куда сохраняется вырезанное расписание группы
# =====================================================

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def clean(x):
    return re.sub(r"\s+", " ", x or "").strip()


def target_date(now):
    """Завтра; если выходной — ближайший понедельник (пт -> пн)."""
    d = now.date() + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def get(url, timeout=(10, 30), **kw):
    """Запрос с проверкой сертификата; если у сайта проблемный сертификат — без проверки
    (мы только читаем публичные данные и ничего не отправляем)."""
    try:
        return requests.get(url, headers=HEADERS, timeout=timeout, **kw)
    except requests.exceptions.SSLError:
        import urllib3
        urllib3.disable_warnings()
        return requests.get(url, headers=HEADERS, timeout=timeout, verify=False, **kw)


def get_retry(url, tries=4, timeout=(20, 120)):
    """Для медленного сайта: несколько попыток с растущей паузой."""
    import time
    for i in range(tries):
        try:
            return get(url, timeout=timeout)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            print(f"попытка {i + 1}/{tries}: {type(e).__name__}", file=sys.stderr)
            if i == tries - 1:
                raise
            time.sleep(5 * (i + 1))


# ---------------------- РАСПИСАНИЕ ----------------------
# PDF университета — это картинка без текста. Скрипт находит на ней блок вашей
# группы (по образцу заголовка header_template.png) и вырезает его в schedule.png.
def render_pdf(data):
    import io, numpy as np, pdfplumber
    pages = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            img = page.to_image(resolution=96).original.convert("RGB")
            pages.append(np.array(img)[:, :, ::-1].copy())      # RGB -> BGR
    return pages


def yellow_bars(im):
    """Жёлтые заголовки блоков групп: [(x, y, w, h), ...]"""
    import cv2
    H, W = im.shape[:2]
    mask = cv2.inRange(cv2.cvtColor(im, cv2.COLOR_BGR2HSV), (10, 120, 200), (35, 255, 255))
    _, _, st, _ = cv2.connectedComponentsWithStats(mask)
    return [tuple(map(int, r[:4])) for r in st[1:]
            if .25 * W < r[2] < .4 * W and .01 * W < r[3] < .03 * W]


def crop_group_block(im, template_path, min_score=0.75, debug=False):
    """Возвращает картинку блока группы или None."""
    import cv2
    tpl = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
    bars = yellow_bars(im)
    best, best_bar = 0.0, None
    for x, y, w, h in bars:
        g = cv2.cvtColor(im[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
        g = cv2.resize(g, (tpl.shape[1], tpl.shape[0]))
        sc = float(cv2.matchTemplate(g, tpl, cv2.TM_CCOEFF_NORMED)[0][0])
        if sc > best:
            best, best_bar = sc, (x, y, w, h)
    if debug:
        print(f"найдено заголовков: {len(bars)}, лучшее совпадение: {best:.2f}")
    if best_bar is None or best < min_score:
        return None
    x, y, w, h = best_bar
    below = [by for _, by, _, _ in bars if by > y + 2 * h]
    bottom = min(below) - 3 if below else min(im.shape[0], y + int(0.6 * w))
    crop = im[max(0, y - 1):bottom, max(0, x - 1):x + w + 1]
    return cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)


def get_schedule(now, out, debug=False):
    import cv2
    day = target_date(now)
    url = PDF_URL.format(d=day.strftime("%d.%m.%Y"))
    res = {"date": day.isoformat(), "pdf": url, "lessons": [], "image": None}
    r = get_retry(url)
    if r.status_code != 200 or not r.content.startswith(b"%PDF"):
        res.update(pdf=None, note=f"Расписание на {day.strftime('%d.%m')} ещё не опубликовано.")
        return res
    template = Path(__file__).with_name("header_template.png")
    for page in render_pdf(r.content):
        block = crop_group_block(page, template, debug=debug)
        if block is not None:
            cv2.imwrite(str(out / IMAGE_NAME), block)
            res["image"] = IMAGE_NAME
            return res
    res["note"] = f"Блок группы {GROUP} не найден в PDF — откройте файл по ссылке."
    return res


# ---------------------- НОВОСТИ ----------------------
def strip_tags(s):
    return clean(re.sub(r"<[^>]+>", " ", s or ""))


def short(s, n=220):
    s = clean(s)
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


def news_from_rss():
    for path in ("feed", "rss", "rss.xml", "?feed=rss2", "news/rss"):
        try:
            r = get(urljoin(BASE, path), timeout=(5, 10))
            if r.status_code != 200 or b"<item" not in r.content[:200000]:
                continue
            items = []
            for it in ET.fromstring(r.content).iter("item"):
                try:
                    date = parsedate_to_datetime(it.findtext("pubDate")).date().isoformat()
                except Exception:
                    date = ""
                items.append({"title": clean(it.findtext("title")), "date": date,
                              "summary": short(strip_tags(it.findtext("description"))),
                              "url": clean(it.findtext("link"))})
            if items:
                return items[:NEWS_LIMIT]
        except Exception:
            continue
    return []


def news_from_html():
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(get(BASE).text, "html.parser")
    seen, items = set(), []
    for a in soup.find_all("a", href=True):
        title = clean(a.get_text(" "))
        href = urljoin(BASE, a["href"])
        if len(title) < 20 or href in seen or not re.search(r"news|novost|article|post|/20\d\d", href, re.I):
            continue
        seen.add(href)
        box = a.find_parent(["article", "li", "div"]) or a
        text = clean(box.get_text(" "))
        m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", text)
        date = f"{m[3]}-{m[2]}-{m[1]}" if m else ""
        p = box.find("p")
        summary = short(p.get_text(" ")) if p and clean(p.get_text()) != title else ""
        items.append({"title": title, "date": date, "summary": summary, "url": href})
        if len(items) >= NEWS_LIMIT:
            break
    return items


def get_news():
    return news_from_rss() or news_from_html()


# ---------------------- MAIN ----------------------
def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print("записан", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=".")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    now, fails = datetime.now(TZ), 0

    try:
        save(out / "schedule.json", get_schedule(now, out, a.debug))
    except Exception as e:
        fails += 1
        print("Ошибка расписания:", repr(e), file=sys.stderr)
    try:
        news = get_news()
        if news:
            save(out / "news.json", news)
        else:
            fails += 1
            print("Новости не найдены — старый news.json оставлен.", file=sys.stderr)
    except Exception as e:
        fails += 1
        print("Ошибка новостей:", repr(e), file=sys.stderr)
    sys.exit(1 if fails == 2 else 0)


if __name__ == "__main__":
    main()
