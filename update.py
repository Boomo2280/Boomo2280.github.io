#!/usr/bin/env python3
"""Обновляет schedule.json и news.json для студенческого портала.

Запуск:  python update.py            (файлы пишутся рядом со скриптом)
         python update.py --out data (писать в папку data)
         python update.py --debug    (показать, что скрипт видит в PDF и на сайте)
"""
import argparse, html as html_lib, json, re, sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests

BASE = "https://kf.mauniver.ru/"
GROUP = "1-ТЭСИС"                            
PDF_URL = BASE + "raspisanie/{d}_s.pdf"     
NEWS_LIMIT = 8
TZ = ZoneInfo("Europe/Moscow")
IMAGE_NAME = "schedule.png"      #


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



def decode(content):
    """Сайт отдаёт UTF-8, но requests без charset в заголовках путает кодировку («кракозябры»)."""
    for enc in ("utf-8", "cp1251"):
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def fix_mojibake(s):
    """Чинит текст вида 'Ð\x92Ñ\x81Ðµ' (UTF-8, прочитанный как latin-1) -> 'Все'."""
    if not isinstance(s, str) or not re.search(r"[ÐÑ]", s):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def strip_tags(s):
    return clean(html_lib.unescape(re.sub(r"<[^>]+>", " ", s or "")))


def short(s, n=200):
    s = clean(s)
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


SKIP_TITLE = re.compile(r"^(все новости|архив|читать|подробнее|далее|ещё|еще)", re.I)
ID_RE = re.compile(r"^(\d{2})(\d{2})(\d{2})-(\d+)$")


def school_year_codes(now):
    """Текущий и прошлый учебный год в формате сайта: 2026-27 -> '2627'."""
    start = now.year % 100 if now.month >= 9 else now.year % 100 - 1
    return [f"{start:02d}{start + 1:02d}", f"{start - 1:02d}{start:02d}"]


def news_from_txt(code):
    r = get_retry(urljoin(BASE, f"novosti/{code}.txt"), tries=3)
    if r.status_code != 200:
        return []
    lines = re.split(r"\r?\n", decode(r.content))
    items = []
    for i in range(0, len(lines) - 2, 4):
        m = ID_RE.match(lines[i].strip())
        if not m:
            continue
        nid, img = lines[i].strip(), lines[i + 2].strip()
        items.append({
            "title": strip_tags(lines[i + 1]),
            "date": f"20{m[1]}-{m[2]}-{m[3]}",
            "summary": short(strip_tags(lines[i + 3] if i + 3 < len(lines) else "")),
            "url": urljoin(BASE, f"novosti/{nid}/{nid}.html"),
            "image": urljoin(BASE, f"novosti/{nid}/original/{img}.jpg") if img else "",
        })
    return items


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


def get_news(out, debug=False, now=None):
    items = []
    for code in school_year_codes(now or datetime.now(TZ)):
        try:
            items += news_from_txt(code)
        except Exception as e:
            print(f"новости {code}.txt не загружены:", repr(e), file=sys.stderr)
        if len(items) >= NEWS_LIMIT:
            break
    items = items[:NEWS_LIMIT]
    for it in items:
        it["title"] = fix_mojibake(it["title"])
        it["summary"] = fix_mojibake(it["summary"])
        if it.get("image"):
            it["image"] = save_image(it["image"], out)
    keep = {Path(i["image"]).name for i in items if i.get("image", "").startswith("news_img/")}
    for f in (out / "news_img").glob("*.jpg") if (out / "news_img").exists() else []:
        if f.name not in keep:
            f.unlink()
    return items


def repair_old_news(path):
    """Если новости не обновились, хотя бы чиним «кракозябры» в старом news.json."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        fixed = [{**i, "title": fix_mojibake(i.get("title", "")), "summary": fix_mojibake(i.get("summary", ""))} for i in data]
        fixed = [i for i in fixed if not SKIP_TITLE.match(i["title"])]      # убираем пункты меню («Все новости…»)
        if fixed != data:
            save(path, fixed)
            print("старый news.json: кракозябры исправлены")
    except Exception:
        pass



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
        news = get_news(out, debug)
        if news:
            save(out / "news.json", news)
        else:
            fails += 1
            print("Новости не найдены — старый news.json оставлен.", file=sys.stderr)
            repair_old_news(out / "news.json")
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
