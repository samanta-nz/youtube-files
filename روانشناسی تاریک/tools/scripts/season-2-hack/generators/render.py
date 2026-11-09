# -*- coding: utf-8 -*-
"""Renderer: 30 cinematic Persian slides for a YouTube video (1920x1080)."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H = 1920, 1080
BASE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(BASE, "assets", "fonts")
OUT = os.path.join(BASE, "build")
REC = {}
os.makedirs(OUT, exist_ok=True)

INK = (8, 10, 15)
INK2 = (16, 20, 28)
RED = (206, 42, 62)
RED_D = (124, 22, 36)
WHITE = (243, 245, 248)
MUTED = (154, 164, 178)
OK_G = (86, 198, 148)
GOLD = (208, 172, 110)

DIR = {"direction": "rtl", "language": "fa"}
_fonts = {}


def font(size, weight="Regular"):
    k = (size, weight)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(os.path.join(F, "Vazirmatn-%s.ttf" % weight), size)
    return _fonts[k]


def fa_num(n):
    return str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def tw(d, s, f):
    return d.textlength(s, font=f, **DIR)


def wrap(d, text, f, maxw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if tw(d, t, f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_rtl(d, xy, text, f, fill, maxw=None, lh=1.55, align="right", spacing=0):
    x, y = xy
    lines = wrap(d, text, f, maxw) if maxw else [text]
    step = int(f.size * lh)
    anchor = {"right": "ra", "center": "ma", "left": "la"}[align]
    for ln in lines:
        d.text((x, y), ln, font=f, fill=fill, anchor=anchor, **DIR)
        y += step + spacing
    return y


# --------------------------------------------------------------- backgrounds
def cover_crop(im, w=W, h=H):
    r = max(w / im.width, h / im.height)
    n = im.resize((int(im.width * r + 1), int(im.height * r + 1)), Image.LANCZOS)
    return n.crop(((n.width - w) // 2, (n.height - h) // 2, (n.width - w) // 2 + w, (n.height - h) // 2 + h))


def grain(im, amount=6.0):
    a = np.asarray(im).astype(np.int16)
    noise = np.random.normal(0, amount, (a.shape[0], a.shape[1], 1))
    return Image.fromarray(np.clip(a + noise, 0, 255).astype(np.uint8))


def vignette(im, strength=0.5):
    w, h = im.size
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w * 0.66)) ** 2 + ((yy - h / 2) / (h * 0.66)) ** 2)
    m = np.clip(1 - strength * np.clip(r - 0.4, 0, 2) ** 1.4, 0, 1)
    return Image.fromarray(np.clip(np.asarray(im).astype(np.float32) * m[..., None], 0, 255).astype(np.uint8))


def hgrad_scrim(im, side="right", dark=0.93, span=0.8):
    w = im.size[0]
    t = np.linspace(0, 1, w)
    if side == "right":
        t = t
    else:
        t = 1 - t
    t = np.clip((t - (1 - span)) / span, 0, 1) ** 1.3
    m = (1 - dark) + dark * t
    return Image.fromarray(np.clip(np.asarray(im).astype(np.float32) * m[None, :, None], 0, 255).astype(np.uint8))


def red_glow(im, pos=(0.15, 0.2), radius=0.5, alpha=46, color=RED, blur=0.11, blend=0.6):
    w, h = im.size
    lay = Image.new("L", (w, h), 0)
    g = ImageDraw.Draw(lay)
    R = int(w * radius)
    g.ellipse([pos[0] * w - R, pos[1] * h - R, pos[0] * w + R, pos[1] * h + R], fill=alpha)
    lay = lay.filter(ImageFilter.GaussianBlur(int(w * blur)))
    glow = Image.new("RGB", (w, h), color)
    return Image.composite(Image.blend(im, glow, blend), im, lay)


def photo_bg(path, side="right", dark=0.94):
    im = cover_crop(Image.open(path).convert("RGB"))
    im = ImageEnhance.Color(im).enhance(0.9)
    im = ImageEnhance.Contrast(im).enhance(1.07)
    im = ImageEnhance.Brightness(im).enhance(1.02)
    im = hgrad_scrim(im, side=side, dark=dark)
    im = red_glow(im, pos=(0.12, 0.86) if side == "right" else (0.88, 0.15), alpha=24)
    im = vignette(im, 0.3)
    return grain(im, 5.5)


def dark_bg(layout="a"):
    arr = np.zeros((H, W, 3), np.float32)
    arr[:] = np.array(INK2, np.float32)
    yy = np.linspace(0, 1, H)[:, None]
    arr *= (0.5 + 0.5 * (1 - yy))[..., None]
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    im = red_glow(im, pos=(0.06, 0.92) if layout == "a" else (0.96, 0.06), alpha=38, radius=0.65, blend=0.55)
    # soft diagonal light sweep
    beam = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(beam)
    bd.polygon([(W * 0.55, 0), (W * 0.95, 0), (W * 1.05, H), (W * 0.6, H)], fill=26)
    beam = beam.filter(ImageFilter.GaussianBlur(140))
    im = Image.composite(Image.new("RGB", (W, H), (78, 88, 110)), im, beam)
    return grain(im, 4.5)


# --------------------------------------------------------------- chrome
def chrome(im, page, tag="روان‌شناسی تاریک · دست‌کاری پنهان عواطف", total=30):
    d = ImageDraw.Draw(im)
    d.line([(W - 196, 74), (W - 96, 74)], fill=RED, width=4)
    d.text((W - 96, 92), tag, font=font(25, "Medium"), fill=(170, 178, 192), anchor="ra", **DIR)
    d.line([(96, H - 100), (W - 96, H - 100)], fill=(38, 43, 53), width=1)
    d.text((96, H - 64), "DARK PSYCHOLOGY", font=font(22, "Medium"), fill=(112, 120, 134), anchor="la")
    d.text((W - 96, H - 66), "%s از %s" % (fa_num(page), fa_num(total)), font=font(24, "Medium"),
           fill=(146, 155, 170), anchor="ra", **DIR)
    return im


def headline_glow(im):
    lay = im.filter(ImageFilter.GaussianBlur(60))
    return Image.blend(im, lay, 0.25)


def kicker(d, text, x=W - 152, y=208, color=RED, size=28):
    d.text((x, y), text, font=font(size, "Bold"), fill=color, anchor="ra", **DIR)
    d.line([(x + 24, y + size // 2 + 4), (x + 24 + 86, y + size // 2 + 4)], fill=color, width=3)
    return y


def save(im, idx):
    im.convert("RGB").save(os.path.join(OUT, "%02d.png" % idx), optimize=True)


# --------------------------------------------------------------- layouts
def cover(idx, title, sub, kick, bg):
    REC[idx] = bg
    im = photo_bg(bg, side="right", dark=0.93)
    d = ImageDraw.Draw(im)
    kicker(d, kick, y=244)
    y = draw_rtl(d, (W - 152, 320), title, font(118, "Black"), WHITE, maxw=1080, lh=1.26)
    y += 22
    d.line([(W - 152, y), (W - 152 - 230, y)], fill=RED, width=6)
    draw_rtl(d, (W - 152, y + 44), sub, font(41, "Regular"), (198, 206, 218), maxw=980, lh=1.62)
    chrome(im, idx)
    save(im, idx)


def section(idx, title, sub, bg, kick="فصل اول", num=None):
    REC[idx] = bg
    im = photo_bg(bg, side="right", dark=0.92)
    d = ImageDraw.Draw(im)
    kicker(d, kick, y=272)
    y = 340
    if num:
        d.text((W - 152, y), num, font=font(140, "Black"), fill=RED, anchor="ra", **DIR)
        y += 160
    y = draw_rtl(d, (W - 152, y), title, font(100, "Black"), WHITE, maxw=1020, lh=1.28)
    y += 20
    d.line([(W - 152, y), (W - 152 - 175, y)], fill=RED, width=6)
    if sub:
        draw_rtl(d, (W - 152, y + 42), sub, font(39, "Regular"), (204, 212, 224), maxw=960, lh=1.62)
    im = Image.blend(im, im.filter(ImageFilter.GaussianBlur(14)), 0.16)
    chrome(im, idx)
    save(im, idx)


def bullets(idx, title, items, bg=None, kick="فصل اول", layout="a", note=None):
    REC[idx] = bg
    if bg:
        im = photo_bg(bg, side="right", dark=0.985)
        im = ImageEnhance.Brightness(im).enhance(0.72)
        im = hgrad_scrim(im, side="right", dark=0.55, span=0.62)
    else:
        im = dark_bg(layout)
    d = ImageDraw.Draw(im)
    kicker(d, kick, y=172)
    y = draw_rtl(d, (W - 152, 232), title, font(76, "Black"), WHITE, maxw=1240, lh=1.3)
    y += 26
    d.line([(W - 152, y), (W - 152 - 135, y)], fill=RED, width=5)
    y += 56
    fs = 43 if len(items) <= 4 else 39
    for i, it in enumerate(items):
        cy = y + fs // 2 + 6
        bx = W - 152
        d.rectangle([bx - 18, cy - 18, bx, cy + 18], fill=RED)
        d.text((bx - 9, cy + 1), fa_num(i + 1), font=font(21, "Bold"), fill=WHITE, anchor="mm", **DIR)
        y = draw_rtl(d, (bx - 52, y), it, font(fs, "Medium"), (226, 231, 238), maxw=1290, lh=1.5)
        y += 24
    if note:
        y += 6
        d.line([(W - 204, y), (W - 204 - 74, y)], fill=GOLD, width=3)
        draw_rtl(d, (W - 204, y + 20), note, font(33, "Medium"), GOLD, maxw=1280, lh=1.5)
    chrome(im, idx)
    save(im, idx)


def quote(idx, text, source=None, bg=None, kick="نقل قول"):
    REC[idx] = bg
    im = photo_bg(bg, side="left", dark=0.9) if bg else dark_bg("b")
    if bg:
        im = ImageEnhance.Brightness(im).enhance(1.0)
    d = ImageDraw.Draw(im)
    kicker(d, kick, x=152, y=246, size=27)
    d.text((148, 296), "”", font=font(210, "Black"), fill=RED, anchor="la")
    y = draw_rtl(d, (152, 470), text, font(68, "Bold"), WHITE, maxw=1180, lh=1.55, align="left")
    if source:
        y += 26
        d.line([(152, y), (152 + 150, y)], fill=RED, width=5)
        draw_rtl(d, (152, y + 26), source, font(33, "Medium"), MUTED, maxw=1050, lh=1.5, align="left")
    chrome(im, idx)
    save(im, idx)


def steps(idx, title, items, kick="زنجیره دستکاری", bg=None):
    REC[idx] = bg
    im = photo_bg(bg, side="right", dark=0.96) if bg else dark_bg("a")
    if bg:
        im = ImageEnhance.Brightness(im).enhance(0.72)
    d = ImageDraw.Draw(im)
    kicker(d, kick, y=172)
    y = draw_rtl(d, (W - 152, 232), title, font(72, "Black"), WHITE, maxw=1280, lh=1.3)
    y += 62
    n = len(items)
    gap = 32
    bw = (W - 304 - gap * (n - 1)) / n
    bh = 452
    for i, (t, desc) in enumerate(items):
        x1 = W - 152 - (i + 1) * bw - i * gap
        d.rectangle([x1, y, x1 + bw, y + bh], fill=(19, 23, 31))
        d.rectangle([x1, y, x1 + bw, y + 7], fill=RED if i == n - 1 else RED_D)
        d.text((x1 + bw - 36, y + 46), fa_num(i + 1), font=font(62, "Black"),
               fill=RED if i < n - 1 else WHITE, anchor="ra", **DIR)
        ty = draw_rtl(d, (x1 + bw - 36, y + 152), t, font(41, "Black"), WHITE, maxw=bw - 72, lh=1.36)
        draw_rtl(d, (x1 + bw - 36, ty + 16), desc, font(29, "Regular"), (174, 183, 196), maxw=bw - 72, lh=1.55)
    chrome(im, idx)
    save(im, idx)


def compare(idx, title, a, b, bg=None):
    REC[idx] = bg
    im = photo_bg(bg, side="right", dark=0.96) if bg else dark_bg("b")
    if bg:
        im = ImageEnhance.Brightness(im).enhance(0.72)
    d = ImageDraw.Draw(im)
    kicker(d, "تفاوت کلیدی", y=172)
    y = draw_rtl(d, (W - 152, 232), title, font(70, "Black"), WHITE, maxw=1200, lh=1.3)
    y += 60
    pw = (W - 304 - 36) / 2
    ph = 486
    for i, (label, text, col) in enumerate([(a[0], a[1], OK_G), (b[0], b[1], RED)]):
        x1 = W - 152 - (i + 1) * pw - i * 36
        d.rectangle([x1, y, x1 + pw, y + ph], fill=(19, 23, 31))
        d.rectangle([x1, y, x1 + pw, y + 7], fill=col)
        d.text((x1 + pw - 40, y + 48), label, font=font(41, "Black"), fill=col, anchor="ra", **DIR)
        draw_rtl(d, (x1 + pw - 40, y + 130), text, font(34, "Medium"), (224, 229, 236), maxw=pw - 80, lh=1.62)
    chrome(im, idx)
    save(im, idx)


def plate(idx, title, sub, bg, kick="فصل اول", tag="صحنه"):
    """Photo-led frame: image on the left, compact text block on the right."""
    REC[idx] = bg
    im = photo_bg(bg, side="right", dark=0.95)
    d = ImageDraw.Draw(im)
    kicker(d, kick, y=252)
    y = draw_rtl(d, (W - 152, 322), title, font(88, "Black"), WHITE, maxw=880, lh=1.28)
    y += 22
    d.line([(W - 152, y), (W - 152 - 160, y)], fill=RED, width=6)
    draw_rtl(d, (W - 152, y + 40), sub, font(37, "Regular"), (203, 210, 222), maxw=830, lh=1.6)
    im = Image.blend(im, im.filter(ImageFilter.GaussianBlur(14)), 0.14)
    chrome(im, idx)
    save(im, idx)


def ending(idx, big, sub, bg, kick="ادامه دارد"):
    REC[idx] = bg
    im = photo_bg(bg, side="right", dark=0.88)
    d = ImageDraw.Draw(im)
    kicker(d, kick, y=296)
    y = draw_rtl(d, (W - 152, 366), big, font(106, "Black"), WHITE, maxw=1020, lh=1.28)
    y += 20
    d.line([(W - 152, y), (W - 152 - 205, y)], fill=RED, width=6)
    draw_rtl(d, (W - 152, y + 42), sub, font(38, "Regular"), (206, 212, 222), maxw=940, lh=1.6)
    chrome(im, idx)
    save(im, idx)


# --------------------------------------------------------------- content
B = lambda n: os.path.join(BASE, "assets", "bg-jpg", "bg%02d.jpg" % n)
has = lambda n: os.path.exists(B(n))
P = lambda n: os.path.join(BASE, "assets", "bg-jpg", "%s.jpg" % n)
ph = lambda *ns: next(B(n) for n in ns if has(n))

cover(1, "روان‌شناسی تاریک", "دست‌کاری پنهان عواطف — اصولی که بانفوذترین آدم‌های تاریخ به کار می‌بردند",
      "خلاصه کتاب · بخش اول", ph(1))

section(2, "دانش، قدرت است",
        "کسی که اصول روان‌شناسی را می‌فهمد، کلید تأثیر گذاشتن بر انسان‌ها را در دست دارد.",
        P("v03"), kick="مقدمه")

bullets(3, "روان‌شناسی، زیربنای همه‌چیز", [
    "تبلیغات و امور مالی",
    "جُرم و مذهب",
    "از عشق تا نفرت",
    "کلیدی که فقط افراد بسیار کمی صاحبش هستند",
], kick="مقدمه", layout="a")

quote(4, "این دانش لابه‌لای صفحه‌های مجله‌های تخصصی و پیچیده پنهان شده و از دسترس عموم دور مانده است.",
      "مقدمه کتاب", bg=P("v03"))

bullets(5, "چرا این کتاب؟", [
    "عصاره‌ای به‌روز از قدرتمندترین اصول روان‌شناسی",
    "بدون نیاز به دانش تخصصی؛ فقط مشتاقِ یادگیری",
    "نمونه‌های واقعی از کاربرد این روش‌ها در طول تاریخ",
    "تمرین: آنچه می‌خوانید را به کار ببندید",
], kick="چرا این کتاب", bg=P("v02"), layout="b")

section(6, "دنیای روان‌شناسی تاریک",
        "شگِردهایی که بانفوذترین افراد تاریخ به کار می‌بردند؛ چیزی شبیه جادوی سیاه روان‌شناختی.",
        ph(6))

compare(7, "امروز دو انتخاب داری",
        ("انتخاب اول", "بی‌خبر بمانی از وجود این نیرو و خطر تبدیل شدن به قربانی بعدی‌اش را بپذیری"),
        ("انتخاب دوم", "کنترل وضعیتت را به دست بگیری و یاد بگیری از خودت و عزیزانت محافظت کنی"), bg=P("v06"))

bullets(8, "قدرت بزرگ، مسئولیت بزرگ", [
    "این کتاب می‌تواند قدرتمندترین راهنمای دفاعی باشد",
    "یا سلاحی شود که در زندگی برایت امتیاز می‌آورد",
    "ایده‌ها صرفاً ابزارند؛ با آن‌ها هر چه می‌خواهی بساز",
    "این کتاب برای آدم‌های زودرنج نوشته نشده است",
], kick="هشدار", layout="a", note="هشدار لازم را دریافت کرده‌اید.")

section(9, "دست‌کاری پنهان عواطف",
        "نخستین و بنیادی‌ترین موضوع این کتاب؛ کلیدی برای فهم تمام روش‌های بعدی.",
        ph(9, 1), kick="فصل اول", num="۰۱")

quote(10, "دست‌کاری پنهان عواطف یعنی یک نفر با روشی فریب‌کارانه و دور از چشم طرف مقابل، بر افکار و احساساتش اثر بگذارد.",
      "تعریف · فصل اول", bg=ph(7))

steps(11, "سه جزء این عنوان", [
    ("پنهان", "قربانی نه می‌داند تحت تأثیر قرار گرفته، نه می‌فهمد چطور و نه انگیزه را حدس می‌زند"),
    ("عاطفی", "هدف، تغییرِ وضعیت احساسی فرد و درکِ او از واقعیت است"),
    ("دست‌کاری", "فرایندی پنهانی و فریب‌کارانه که بیرون از آگاهی فرد رخ می‌دهد"),
], kick="تعریف", bg=P("v03"))

quote(12, "دست‌کاری پنهان عواطف مثل بمب‌افکن رادارگریز در جنگ روانی است: تا وقتی خیلی دیر شده، نه شناسایی می‌شود و نه فرصتی برای دفاع می‌گذارد.",
      "فصل اول · تعریف", bg=ph(13))

bullets(13, "چرا دست‌کاری‌کنندگان عواطف را هدف می‌گیرند؟", [
    "احساساتِ انسان، کلید دسترسی به بقیه جنبه‌های شخصیت اوست",
    "اگر کسی کنترل عواطف را به دست بگیرد، کنترل کامل را به دست گرفته",
    "دست بردن در احساسات کسی، مثل بریدن رگ گردن اوست",
    "احساسات، دروازه‌ای است که پنهانی باز می‌شود",
], kick="هدف اصلی", bg=P("v01"), layout="b")

compare(14, "تأثیرگذاری یا دست‌کاری؟",
        ("تأثیرگذاری", "«دوست دارم کمکت کنم تصمیم‌هایی بگیری که به نفع خودت باشند.»"),
        ("دست‌کاری", "«می‌خواهم بی‌سروصدا کنترلَت کنم تا خودم سود ببرم.»"), bg=P("v02"))

bullets(15, "چهار میدان اصلی دست‌کاری", [
    "محیط کار — رئیسی که بی‌دلیل روشن، ترس یا گناه ایجاد می‌کند",
    "روابط شخصی — دوستی که پنهانی احساس وظیفه می‌سازد",
    "روابط عاشقانه — رایج‌ترین و مرگ‌بارترین شکل",
    "خانواده — مسئله‌سازترین فضا برای سوءاستفاده",
], kick="میدان‌ها", bg=P("v05"), layout="a")

section(16, "شریک عاطفی کنترل‌گر",
        "چرا کنترل را پنهانی اعمال می‌کند؟ چون کنترل آشکار، قربانی را به فکر فرار می‌اندازد.",
        ph(9, 1))

bullets(17, "دوستِ به‌اصطلاح صمیمی", [
    "پنهانی در دوستش احساس گناه ایجاد می‌کند",
    "دلسوزی و ترحم را به ابزار نفوذ تبدیل می‌کند",
    "احساس وظیفه‌شناسی می‌سازد، بدون اینکه کسی متوجه شود",
    "قربانی حتی نمی‌تواند توضیح بدهد چرا این‌طور رفتار می‌کند",
], kick="تیپ شخصیتی", bg=P("v04"), layout="b")

section(18, "رئیس و محیط کار",
        "آدم‌هایی که هرگز نفهمیدند آن احساس گناه و ترس از کجا سرچشمه گرفته است.",
        ph(8))

bullets(19, "خانواده: خطرناک‌ترین میدان", [
    "تعهد اجتماعی برای کمک به اعضای خانواده از قبل وجود دارد",
    "با پیوند خونی، کنترل و نفوذ چندین برابر می‌شود",
    "وقتی آمادگیِ تأثیرپذیری با شگِردهای دست‌کاری ترکیب شود…",
    "نتیجه: قربانی‌ای که به‌آسانی شکل دلخواه می‌گیرد",
], bg=ph(10), kick="هشدار", layout="a")

section(20, "روش‌های دست‌کاری پنهان",
        "تمام هدف این است که تا حد ممکن ناشناخته بماند؛ این بخش، پرده از همین دنیای مخفی برمی‌دارد.",
        P("v02"), kick="شگِردها")

section(21, "بمباران عشق", "ناگهانی، شدید و با اصرار فراوان — در روزهای نخست آشنایی.",
        ph(12), kick="شگِرد اول")

bullets(22, "منطق بمباران عشق", [
    "ایجاد اعتماد، محبت و تمایل شدید به همراهی",
    "پایین آوردن سپرهای دفاعی قربانی",
    "افزایش وابستگی و ساختن تصویری مثبت از رابطه",
    "دوزِ مناسب برای هر هدف: تنها و درمانده، یا با ثبات",
], bg=P("v09"), layout="a", note="مثل پزشکی که داروی مناسب را با دوز مناسب تجویز می‌کند.", kick="شگرد اول")

quote(23, "رفتاری با پیامدِ منفی، در پوششِ چیزی کاملاً مثبت پنهان می‌شود؛ و همین آن را غیرقابل تشخیص می‌کند.",
      "درس اول بمباران عشق", bg=ph(12))

section(24, "تقویت رفتار", "زنجیره‌ای از شگِردها: بمباران عشق ← تقویت مثبت ← تقویت مثبت متناوب",
        ph(6), kick="شگِرد دوم")

steps(25, "زنجیره سه‌گامی", [
    ("بمباران عشق", "ابراز شدید، بی‌قیدوشرط و بی‌دلیل احساسات مثبت در روزهای نخست"),
    ("تقویت مثبت", "واکنش مثبت نگه داشته می‌شود تا قربانی رفتار دلخواه را انجام دهد"),
    ("تقویت متناوب", "پاداش گاهی می‌آید و گاهی نه؛ نتیجه: اشتیاق ناخودآگاه"),
], kick="زنجیره دستکاری", bg=P("v10"))

bullets(26, "تقویت مثبت چگونه کار می‌کند", [
    "اگر می‌خواهد قربانی مرتب تلفن بزند، فقط بعد از تماس واکنش مثبت نشان می‌دهد",
    "قربانی نمی‌فهمد توجه مثبت، حساب‌شده علیه او استفاده می‌شود",
    "ناخودآگاه برای تجربه دوباره آن حس خوشایند، مطابق میل او رفتار می‌کند",
], kick="شگرد دوم", layout="b")

quote(27, "در تقویت متناوب، پاداش غیرقابل‌پیش‌بینی است؛ و همین قربانی را به تلاشی بی‌پایان برای گرفتن واکنش خوب وامی‌دارد.",
      "تقویت مثبت متناوب", bg=P("v09"))

bullets(28, "چرا غیرقابل‌پیش‌بینی بودن خطرناک است", [
    "اشتیاقی عمیق و ناخودآگاه برای دریافت توجه مثبت شکل می‌گیرد",
    "قربانی به هر راهی متوسل می‌شود تا واکنش خوب بگیرد",
    "سوءاستفاده‌گر رفتار او را در جهت دلخواهش شکل می‌دهد",
    "قربانی هیچ درکی ندارد که چه می‌کند و چرا",
], bg=P("v04"), kick="هشدار", layout="a")

section(29, "انکار واقعیت",
        "ترسناک‌ترین تجربه ممکن: این احساس که داری عقلت را از دست می‌دهی — و کسی عمداً آن را ساخته است.",
        ph(1), kick="شگِرد سوم")

bullets(30, "انکار واقعیت چگونه اعتماد را می‌دزدد", [
    "تدریجی است: رویکرد «آهسته اما پیوسته» تا لو نرود",
    "با زیر سؤال بردن جزئی حافظه قربانی آغاز می‌شود",
    "اعتماد به عقل خودت کم می‌شود و به دست‌کاری‌کننده منتقل می‌شود",
    "در پایان، قربانی خودش را مقصر می‌داند",
], bg=P("v08"), kick="شگرد سوم", layout="b", note="ادامه انکار واقعیت، در قسمت بعد.")

import json
json.dump({k: (os.path.basename(v) if v else None) for k, v in REC.items()}, open(os.path.join(BASE, "manifest.json"), "w"), ensure_ascii=False, indent=1)
print("done:", len(os.listdir(OUT)), "frames")
