# -*- coding: utf-8 -*-
"""Brand thumbnail for the audio-book intro: same t06 plate, new copy. 3 variants."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from engine import cover_crop, font, DIR

W, H = 1280, 720
BASE = os.path.dirname(os.path.abspath(__file__))
PL = os.path.join(BASE, "assets", "bg")
OUT = os.path.join(BASE, "thumbs_brand")
os.makedirs(OUT, exist_ok=True)

R = (240, 42, 64)
RD = (150, 12, 28)
WHT = (252, 252, 254)
GLD = (246, 202, 98)
SAFE = 44


def plate(name, clear="right", shift=0.0, dark=0.78, span=0.55,
          bright=1.28, contrast=1.1, sat=1.08):
    im = cover_crop(Image.open(os.path.join(PL, name + ".jpg")).convert("RGB"), W, H)
    if shift:
        w = int(W * (1 - abs(shift)))
        h = int(w * 9 / 16)
        x0 = (W - w) if shift > 0 else 0
        y0 = max(0, (H - h) // 2)
        im = im.crop((x0, y0, x0 + w, y0 + h)).resize((W, H), Image.LANCZOS)
    im = ImageEnhance.Color(im).enhance(sat)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Brightness(im).enhance(bright)
    x = np.linspace(0, 1, W)
    t = x if clear == "right" else 1 - x
    t = np.clip((t - (1 - span)) / span, 0, 1) ** 1.05
    m = (1 - dark) + dark * t
    a = np.asarray(im).astype(np.float32) * m[None, :, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def shadow(im, text, xy, f, fill, anchor="ra", blur=11, alpha=225):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((xy[0] + 2, xy[1] + 8), text, font=f,
                             fill=(0, 0, 0, alpha), anchor=anchor, **DIR)
    return Image.alpha_composite(im, lay.filter(ImageFilter.GaussianBlur(blur)))


def outlined(im, text, xy, f, fill, anchor="ra", w=4):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for dx in range(-w, w + 1, 2):
        for dy in range(-w, w + 1, 2):
            if dx or dy:
                d.text((xy[0] + dx, xy[1] + dy), text, font=f,
                       fill=(5, 5, 8, 255), anchor=anchor, **DIR)
    im = Image.alpha_composite(im, lay)
    ImageDraw.Draw(im).text(xy, text, font=f, fill=fill, anchor=anchor, **DIR)
    return im


def block(im, lines, x, top, maxw, align="right", size=118, gap=8, outline=4, min_size=50):
    """Draw stacked lines starting at `top`; auto-shrink to fit maxw."""
    d = ImageDraw.Draw(im)
    anchor = {"right": "ra", "left": "la", "center": "ma"}[align]
    y = top
    for text, col in lines:
        s = size
        while d.textlength(text, font=font(s, "Black"), **DIR) > maxw and s > min_size:
            s -= 3
        f = font(s, "Black")
        im = shadow(im, text, (x, y), f, col, anchor=anchor)
        im = outlined(im, text, (x, y), f, col, anchor=anchor, w=outline)
        y += int(sum(f.getmetrics()) * 1.02) + gap
    return im, y


def block_fit(im, lines, x, top, bottom, maxw, align="right", size=124, gap=6,
              outline=4, min_size=54):
    """Stack lines between `top` and `bottom`, shrinking until it fits."""
    d = ImageDraw.Draw(im)
    anchor = {"right": "ra", "left": "la", "center": "ma"}[align]
    s_ = size
    while s_ > min_size:
        widths = [d.textlength(t, font=font(s_, "Black"), **DIR) for t, _ in lines]
        hh = [sum(font(s_, "Black").getmetrics()) for _ in lines]
        total = sum(hh) + gap * (len(lines) - 1)
        if max(widths) <= maxw and total <= bottom - top:
            break
        s_ -= 3
    y = top
    for text, col in lines:
        f = font(s_, "Black")
        im = shadow(im, text, (x, y), f, col, anchor=anchor)
        im = outlined(im, text, (x, y), f, col, anchor=anchor, w=outline)
        y += int(sum(f.getmetrics()) * 1.02) + gap
    return im, y


def chip(im, x, y, text, fg=WHT, bg=RD, size=28, align="right"):
    d = ImageDraw.Draw(im)
    f = font(size, "Bold")
    w = d.textlength(text, font=f, **DIR)
    ph, pv = 26, 11
    asc, desc = f.getmetrics()
    h = asc + desc + pv * 2
    box = [x - w - ph * 2, y, x, y + h] if align == "right" else [x, y, x + w + ph * 2, y + h]
    d.rounded_rectangle(box, radius=9, fill=bg)
    d.text((box[2] - ph, y + pv - 1), text, font=f, fill=fg, anchor="ra", **DIR)
    return im, y + h


def bar(im, x, y, width=150, col=R, h=9, align="right"):
    d = ImageDraw.Draw(im)
    d.rectangle([x - width, y, x, y + h] if align == "right" else [x, y, x + width, y + h], fill=col)
    return im


def small(im, x, y, text, size=30, fill=(232, 236, 244), align="right", weight="Bold"):
    d = ImageDraw.Draw(im)
    f = font(size, weight)
    anchor = "ra" if align == "right" else "la"
    im = shadow(im, text, (x, y), f, fill, anchor=anchor, blur=8, alpha=200)
    ImageDraw.Draw(im).text((x, y), text, font=f, fill=fill, anchor=anchor, **DIR)
    return im


def brandmark(im, corner="tl"):
    d = ImageDraw.Draw(im)
    f = font(23, "Bold")
    if corner == "tl":
        d.text((SAFE - 10, 26), "روان‌شناسی تاریک", font=f, fill=(255, 255, 255, 210), anchor="la", **DIR)
        d.line([(SAFE - 10, 64), (SAFE - 10 + 56, 64)], fill=R, width=4)
    return im


def save(im, name):
    im.convert("RGB").save(os.path.join(OUT, name), quality=95, subsampling=0, optimize=True)
    return im


AUDIO = "کتاب صوتی روان‌شناسی تاریک"
PART = "مقدمه و فصل یک"

# ============================================================ A — عنوان سه‌خطی + زیرتیتر + متا
im = plate("t06", clear="right", shift=0.12, dark=0.74, span=0.52, bright=1.25)
CHIP_TOP = H - 148
im, y = block_fit(im, [("شگردهایی که", WHT),
                       ("شما را کنترل", WHT),
                       ("می‌کنند", R)], W - SAFE, 62, CHIP_TOP - 108, maxw=660, size=128, gap=4)
im = small(im, W - SAFE, y + 2, "و باید آگاه باشی", size=38, fill=GLD)
im = bar(im, W - SAFE, y + 74, width=150)
im, _ = chip(im, W - SAFE, CHIP_TOP, AUDIO + " · " + PART, bg=RD)
im = brandmark(im, "tl")
save(im, "A - شگردهایی که شما را کنترل می‌کنند.jpg")

# ============================================================ B — عنوان کوتاه‌تر و درشت‌تر، متا دو خطی
im = plate("t06", clear="right", shift=0.14, dark=0.74, span=0.5, bright=1.25)
im, y = block(im, [("شگردهایی که", WHT),
                   ("کنترلَت می‌کنند", R)], W - SAFE, 108, maxw=700, size=140, gap=8)
im = small(im, W - SAFE, y + 16, "و باید آگاه باشی", size=42, fill=WHT)
im = bar(im, W - SAFE, y + 84, width=150)
im, cb = chip(im, W - SAFE, y + 116, AUDIO, bg=RD)
im = small(im, W - SAFE, cb + 16, PART + "  ·  از: ـــــــــ", size=30, fill=(228, 232, 240))
im = brandmark(im, "tl")
save(im, "B - کنترلَت می‌کنند.jpg")

# ============================================================ C — برند بالا + عنوان وسط + نوار پایین
im = plate("t06", clear="right", shift=0.10, dark=0.72, span=0.55, bright=1.28)
im = small(im, W - SAFE, 52, "روان‌شناسی تاریک", size=34, fill=(240, 240, 245))
im = bar(im, W - SAFE, 100, width=120)
im, y = block(im, [("شگردهایی که شما را", WHT),
                   ("کنترل می‌کنند", R)], W - SAFE, 148, maxw=680, size=118, gap=10)
im = small(im, W - SAFE, y + 10, "و باید آگاه باشی", size=40, fill=GLD)
im, cb = chip(im, W - SAFE, H - 150, PART, bg=RD)
im = small(im, W - SAFE, cb + 14, AUDIO + "  ·  از: ـــــــــ", size=30, fill=(228, 232, 240))
save(im, "C - روایت برند.jpg")

print("brand thumbs:", len(os.listdir(OUT)))
