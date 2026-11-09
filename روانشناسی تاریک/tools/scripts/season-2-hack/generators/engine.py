# -*- coding: utf-8 -*-
"""Shared engine: cinematic Persian slides 1920x1080 (16:9) — dark psychology series."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H = 1920, 1080
BASE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(BASE, "assets", "fonts")
PL = os.path.join(BASE, "assets", "bg")

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


def fit_font(d, text, weight, max_size, maxw, min_size=54, max_lines=1):
    for size in range(max_size, min_size - 1, -2):
        if len(wrap(d, text, font(size, weight), maxw)) <= max_lines:
            return font(size, weight)
    return font(min_size, weight)


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


def vignette(im, strength=0.3):
    w, h = im.size
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w * 0.66)) ** 2 + ((yy - h / 2) / (h * 0.66)) ** 2)
    m = np.clip(1 - strength * np.clip(r - 0.4, 0, 2) ** 1.4, 0, 1)
    return Image.fromarray(np.clip(np.asarray(im).astype(np.float32) * m[..., None], 0, 255).astype(np.uint8))


def hgrad_scrim(im, side="right", dark=0.93, span=0.8):
    w = im.size[0]
    t = np.linspace(0, 1, w) if side == "right" else 1 - np.linspace(0, 1, w)
    t = np.clip((t - (1 - span)) / span, 0, 1) ** 1.3
    m = (1 - dark) + dark * t
    return Image.fromarray(np.clip(np.asarray(im).astype(np.float32) * m[None, :, None], 0, 255).astype(np.uint8))


def red_glow(im, pos=(0.15, 0.2), radius=0.5, alpha=24, color=RED, blur=0.11, blend=0.6):
    w, h = im.size
    lay = Image.new("L", (w, h), 0)
    g = ImageDraw.Draw(lay)
    R = int(w * radius)
    g.ellipse([pos[0] * w - R, pos[1] * h - R, pos[0] * w + R, pos[1] * h + R], fill=alpha)
    lay = lay.filter(ImageFilter.GaussianBlur(int(w * blur)))
    return Image.composite(Image.blend(im, Image.new("RGB", (w, h), color), blend), im, lay)


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
    beam = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(beam)
    bd.polygon([(W * 0.55, 0), (W * 0.95, 0), (W * 1.05, H), (W * 0.6, H)], fill=26)
    beam = beam.filter(ImageFilter.GaussianBlur(140))
    im = Image.composite(Image.new("RGB", (W, H), (78, 88, 110)), im, beam)
    return grain(im, 4.5)


# --------------------------------------------------------------- chrome
class Deck:
    def __init__(self, out_dir, tag, total=30, prefix=""):
        self.out = out_dir
        self.tag = tag
        self.total = total
        self.prefix = prefix
        os.makedirs(out_dir, exist_ok=True)
        self.page = 0

    def chrome(self, im):
        d = ImageDraw.Draw(im)
        d.line([(W - 196, 74), (W - 96, 74)], fill=RED, width=4)
        d.text((W - 96, 92), self.tag, font=font(25, "Medium"), fill=(170, 178, 192), anchor="ra", **DIR)
        d.line([(96, H - 100), (W - 96, H - 100)], fill=(38, 43, 53), width=1)
        d.text((96, H - 64), "DARK PSYCHOLOGY", font=font(22, "Medium"), fill=(112, 120, 134), anchor="la")
        d.text((W - 96, H - 66), "%s از %s" % (fa_num(self.page), fa_num(self.total)),
               font=font(24, "Medium"), fill=(146, 155, 170), anchor="ra", **DIR)
        return im

    def save(self, im):
        im.convert("RGB").save(os.path.join(self.out, "%s%02d.png" % (self.prefix, self.page)), optimize=True)
        return im

    @staticmethod
    def kicker(d, text, x=W - 152, y=208, color=RED, size=28):
        d.text((x, y), text, font=font(size, "Bold"), fill=color, anchor="ra", **DIR)
        d.line([(x + 24, y + size // 2 + 4), (x + 24 + 86, y + size // 2 + 4)], fill=color, width=3)

    # ---------------- layouts ----------------
    def cover(self, title, sub, kick, bg):
        self.page += 1
        im = photo_bg(bg, side="right", dark=0.93)
        d = ImageDraw.Draw(im)
        self.kicker(d, kick, y=244)
        y = draw_rtl(d, (W - 152, 320), title, fit_font(d, title, "Black", 116, 1080, 76, 1), WHITE, maxw=1080, lh=1.34)
        y += 22
        d.line([(W - 152, y), (W - 152 - 230, y)], fill=RED, width=6)
        draw_rtl(d, (W - 152, y + 44), sub, font(41, "Regular"), (198, 206, 218), maxw=980, lh=1.62)
        im = Image.blend(im, im.filter(ImageFilter.GaussianBlur(14)), 0.16)
        return self.save(self.chrome(im))

    def section(self, title, sub, bg, kick=None, num=None):
        self.page += 1
        im = photo_bg(bg, side="right", dark=0.92)
        d = ImageDraw.Draw(im)
        self.kicker(d, kick or self.tag, y=272)
        y = 340
        if num:
            d.text((W - 152, y), num, font=font(140, "Black"), fill=RED, anchor="ra", **DIR)
            y += 160
        f = fit_font(d, title, "Black", 100, 1020, 66, max_lines=2)
        y = draw_rtl(d, (W - 152, y), title, f, WHITE, maxw=1020, lh=1.42)
        y += 30
        d.line([(W - 152, y), (W - 152 - 175, y)], fill=RED, width=6)
        if sub:
            draw_rtl(d, (W - 152, y + 42), sub, font(39, "Regular"), (204, 212, 224), maxw=960, lh=1.62)
        im = Image.blend(im, im.filter(ImageFilter.GaussianBlur(14)), 0.16)
        return self.save(self.chrome(im))

    def bullets(self, title, items, bg=None, kick=None, layout="a", note=None):
        self.page += 1
        if bg:
            im = photo_bg(bg, side="right", dark=0.985)
            im = ImageEnhance.Brightness(im).enhance(0.72)
            im = hgrad_scrim(im, side="right", dark=0.55, span=0.62)
        else:
            im = dark_bg(layout)
        d = ImageDraw.Draw(im)
        self.kicker(d, kick or self.tag, y=172)
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
        return self.save(self.chrome(im))

    def quote(self, text, source=None, bg=None, kick="نقل قول"):
        self.page += 1
        im = photo_bg(bg, side="left", dark=0.9) if bg else dark_bg("b")
        d = ImageDraw.Draw(im)
        self.kicker(d, kick, x=152, y=246, size=27)
        d.text((148, 296), "”", font=font(210, "Black"), fill=RED, anchor="la")
        y = draw_rtl(d, (152, 470), text, font(68, "Bold"), WHITE, maxw=1180, lh=1.55, align="left")
        if source:
            y += 26
            d.line([(152, y), (152 + 150, y)], fill=RED, width=5)
            draw_rtl(d, (152, y + 26), source, font(33, "Medium"), MUTED, maxw=1050, lh=1.5, align="left")
        return self.save(self.chrome(im))

    def steps(self, title, items, kick="زنجیره", bg=None):
        self.page += 1
        im = photo_bg(bg, side="right", dark=0.96) if bg else dark_bg("a")
        if bg:
            im = ImageEnhance.Brightness(im).enhance(0.72)
        d = ImageDraw.Draw(im)
        self.kicker(d, kick, y=172)
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
        return self.save(self.chrome(im))

    def compare(self, title, a, b, bg=None, kick="تفاوت کلیدی"):
        self.page += 1
        im = photo_bg(bg, side="right", dark=0.96) if bg else dark_bg("b")
        if bg:
            im = ImageEnhance.Brightness(im).enhance(0.72)
        d = ImageDraw.Draw(im)
        self.kicker(d, kick, y=172)
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
        return self.save(self.chrome(im))
