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
from urllib.parse import urljoin, urlparse
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
def decode(content):
    """Сайт отдаёт UTF-8, но requests без charset в заголовках путает кодировку («кракозябры»)."""
    for enc in ("utf-8", "cp1251"):
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def strip_tags(s):
    return clean(re.sub(r"<[^>]+>", " ", s or ""))


def short(s, n=200):
    s = clean(s)
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


NEWS_HREF = re.compile(r"/(?:novosti|news)/(?!page|\?)[^/?#]+", re.I)
SKIP_TITLE = re.compile(r"^(все новости|архив|читать|подробнее|далее|ещё|еще)", re.I)


def find_image(box):
    """Картинка новости: <img> (в т.ч. ленивая) или background-image."""
    for img in box.find_all("img"):
        src = img.get("data-src") or img.get("data-lazy-src") or img.get("src") or ""
        if not src and img.get("srcset"):
            src = img["srcset"].split()[0]
        if src and not src.startswith("data:") and not re.search(r"logo|icon|\.svg|sprite", src, re.I):
            return urljoin(BASE, src)
    for el in box.find_all(style=True):
        m = re.search(r"url\(['\"]?([^'\")]+)", el["style"])
        if m:
            return urljoin(BASE, m[1])
    return ""


def parse_rss(content):
    items = []
    for it in ET.fromstring(content).iter("item"):
        try:
            date = parsedate_to_datetime(it.findtext("pubDate")).date().isoformat()
        except Exception:
            date = ""
        enc = it.find("enclosure")
        items.append({"title": clean(it.findtext("title")), "date": date,
                      "summary": short(strip_tags(it.findtext("description"))),
                      "url": clean(it.findtext("link")),
                      "image": enc.get("url", "") if enc is not None else ""})
    return items[:NEWS_LIMIT]


def news_from_html(soup):
    links = [a for a in soup.find_all("a", href=True) if NEWS_HREF.search(urlparse(urljoin(BASE, a["href"])).path)]
    hrefs = {urljoin(BASE, a["href"]).split("#")[0] for a in links}
    order, items = [], {}
    for a in links:
        href = urljoin(BASE, a["href"]).split("#")[0]
        if href not in items:
            items[href] = a
            order.append(href)
    res = []
    for href in order:
        a = items[href]
        # поднимаемся до карточки: пока внутри только эта новость
        box = a
        for _ in range(5):
            par = box.parent
            if par is None or par.name in ("body", "html"):
                break
            inside = {urljoin(BASE, x["href"]).split("#")[0] for x in par.find_all("a", href=True)} & hrefs
            if inside - {href}:
                break
            box = par
        titles = [clean(x.get_text(" ")) for x in box.find_all("a", href=True)
                  if urljoin(BASE, x["href"]).split("#")[0] == href]
        heading = box.find(["h1", "h2", "h3", "h4", "h5"])
        title = clean(heading.get_text(" ")) if heading else ""
        if not title:
            title = max((t for t in titles if not SKIP_TITLE.match(t)), key=len, default="")
        if len(title) < 12 or SKIP_TITLE.match(title):
            continue
        text = clean(box.get_text(" "))
        m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", text)
        slug = re.search(r"/(\d{2})(\d{2})(\d{2})-\d+", href)
        date = f"{m[3]}-{m[2]}-{m[1]}" if m else (f"20{slug[1]}-{slug[2]}-{slug[3]}" if slug else "")
        p = next((clean(x.get_text(" ")) for x in box.find_all("p") if len(clean(x.get_text())) > 30
                  and clean(x.get_text()) != title), "")
        res.append({"title": title, "date": date, "summary": short(p), "url": href, "image": find_image(box)})
        if len(res) >= NEWS_LIMIT:
            break
    return res


def save_image(url, out):
    """Скачивает картинку новости в news_img/ (уменьшенную). Если не вышло — оставляет ссылку."""
    import hashlib
    import cv2, numpy as np
    name = hashlib.md5(url.encode()).hexdigest()[:12] + ".jpg"
    path = out / "news_img" / name
    if path.exists():
        return f"news_img/{name}"
    try:
        r = get_retry(url, tries=2, timeout=(15, 60))
        im = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
        if im is None:
            return url
        h, w = im.shape[:2]
        if w > 640:
            im = cv2.resize(im, (640, int(h * 640 / w)), interpolation=cv2.INTER_AREA)
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 82])[1].tobytes())
        return f"news_img/{name}"
    except Exception as e:
        print("картинка не скачана:", url, repr(e), file=sys.stderr)
        return url


def get_news(out):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(decode(get_retry(BASE).content), "html.parser")
    items = []
    link = soup.find("link", type=re.compile(r"rss|atom", re.I))
    if link and link.get("href"):
        try:
            items = parse_rss(get_retry(urljoin(BASE, link["href"])).content)
        except Exception as e:
            print("RSS не разобран:", repr(e), file=sys.stderr)
    items = items or news_from_html(soup)
    for it in items:
        if it.get("image"):
            it["image"] = save_image(it["image"], out)
    keep = {Path(i["image"]).name for i in items if i.get("image", "").startswith("news_img/")}
    for f in (out / "news_img").glob("*.jpg") if (out / "news_img").exists() else []:
        if f.name not in keep:
            f.unlink()
    return items


# ---------------------- MAIN ----------------------
def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print("записан", path)


def run(out, debug=False):
    """Обновляет файлы в папке out. Возвращает число неудачных частей (0, 1 или 2)."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    now, fails = datetime.now(TZ), 0
    try:
        save(out / "schedule.json", get_schedule(now, out, debug))
    except Exception as e:
        fails += 1
        print("Ошибка расписания:", repr(e), file=sys.stderr)
    try:
        news = get_news(out)
        if news:
            save(out / "news.json", news)
        else:
            fails += 1
            print("Новости не найдены — старый news.json оставлен.", file=sys.stderr)
    except Exception as e:
        fails += 1
        print("Ошибка новостей:", repr(e), file=sys.stderr)
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=".")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    sys.exit(1 if run(a.out, a.debug) == 2 else 0)


if __name__ == "__main__":
    main()
