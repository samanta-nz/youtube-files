# -*- coding: utf-8 -*-
"""10 YouTube thumbnails (1280x720) — Persian, high-CTR layout system.
Layout is computed bottom-up so nothing ever clips or overlaps."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from engine import cover_crop, font, DIR

W, H = 1280, 720
BASE = os.path.dirname(os.path.abspath(__file__))
PL = os.path.join(BASE, "assets", "bg")
OUT = os.path.join(BASE, "thumbs")
os.makedirs(OUT, exist_ok=True)

R = (240, 42, 64)
RD = (150, 12, 28)
WHT = (252, 252, 254)
GLD = (246, 202, 98)

SAFE = 44          # outer margin
CHIP_BOTTOM = H - 46
BAR_H = 9
CHIP_SIZE = 28


# ------------------------------------------------------------------ image
def plate(name, clear="right", shift=0.0, zoom=1.0, dark=0.82, span=0.62,
          bright=1.32, contrast=1.1, sat=1.08, focus_y=0.45):
    im = cover_crop(Image.open(os.path.join(PL, name + ".jpg")).convert("RGB"), W, H)
    if shift or zoom != 1.0:
        # shift > 0 : crop from the right  -> subject moves LEFT
        # shift < 0 : crop from the left   -> subject moves RIGHT (and gets bigger)
        w = int(W * (1 - abs(shift)) / max(zoom, 0.2))
        h = int(w * 9 / 16)
        x0 = (W - w) if shift > 0 else 0
        y0 = max(0, min(H - h, int((H - h) * focus_y)))
        im = im.crop((x0, y0, x0 + w, y0 + h)).resize((W, H), Image.LANCZOS)
    im = ImageEnhance.Color(im).enhance(sat)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Brightness(im).enhance(bright)
    x = np.linspace(0, 1, W)
    t = x if clear == "right" else 1 - x
    t = np.clip((t - (1 - span)) / span, 0, 1) ** 1.05
    m = (1 - dark) + dark * t
    a = np.asarray(im).astype(np.float32) * m[None, :, None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    # gentle bottom shade (keeps badge readable, image intact)
    g = np.linspace(0, 1, H)[:, None]
    m2 = 1 - 0.32 * np.clip((g - 0.7) / 0.3, 0, 1) ** 1.3
    a = np.asarray(im.convert("RGB")).astype(np.float32) * m2[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


# ------------------------------------------------------------------ text
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


def headline(im, lines, x, bottom, maxw, align="right", size=132, lh=1.03,
             gap=2, outline=4, min_size=58):
    """Draw stacked headline whose LAST line's baseline bottom sits at `bottom`."""
    d = ImageDraw.Draw(im)
    s = size
    while s > min_size:
        sizes, heights = [], []
        for text, _ in lines:
            sc = s
            while d.textlength(text, font=font(sc, "Black"), **DIR) > maxw and sc > min_size:
                sc -= 3
            sizes.append(sc)
            heights.append(sum(font(sc, "Black").getmetrics()))
        total = sum(heights) + gap * (len(lines) - 1)
        if total <= bottom - 90:
            break
        s -= 4
    y = bottom - total
    anchor = {"right": "ra", "left": "la", "center": "ma"}[align]
    for (text, col), sc in zip(lines, sizes):
        f = font(sc, "Black")
        im = shadow(im, text, (x, y), f, col, anchor=anchor)
        im = outlined(im, text, (x, y), f, col, anchor=anchor, w=outline)
        y += sum(f.getmetrics()) + gap
    return im


def chip(im, x, text, bottom=CHIP_BOTTOM, fg=WHT, bg=RD, size=CHIP_SIZE, align="right"):
    d = ImageDraw.Draw(im)
    f = font(size, "Bold")
    w = d.textlength(text, font=f, **DIR)
    ph, pv = 26, 11
    asc, desc = f.getmetrics()
    h = asc + desc + pv * 2
    top = bottom - h
    if align == "right":
        box = [x - w - ph * 2, top, x, bottom]
    else:
        box = [x, top, x + w + ph * 2, bottom]
    d.rounded_rectangle(box, radius=9, fill=bg)
    d.text((box[2] - ph, top + pv - 1), text, font=f, fill=fg, anchor="ra", **DIR)
    return im


def bar(im, x, y, width=150, col=R, h=BAR_H, align="right"):
    if align == "right":
        ImageDraw.Draw(im).rectangle([x - width, y, x, y + h], fill=col)
    else:
        ImageDraw.Draw(im).rectangle([x, y, x + width, y + h], fill=col)
    return im


def brand(im, corner="tl"):
    d = ImageDraw.Draw(im)
    f = font(23, "Bold")
    txt = "روان‌شناسی تاریک"
    if corner == "tl":
        d.text((SAFE - 10, 26), txt, font=f, fill=(255, 255, 255, 205), anchor="la", **DIR)
        d.line([(SAFE - 10, 64), (SAFE - 10 + 56, 64)], fill=R, width=4)
    else:
        d.text((W - SAFE + 10, 26), txt, font=f, fill=(255, 255, 255, 205), anchor="ra", **DIR)
        d.line([(W - SAFE - 46, 64), (W - SAFE + 10, 64)], fill=R, width=4)
    return im


def build(idx, plate_name, lines, chip_text, side="right", chip_bg=RD,
          maxw=660, size=136, glow=None, **pk):
    """side = the clear side of the photo; text is placed on that side."""
    im = plate(plate_name, clear=side, **pk)
    x = (W - SAFE) if side == "right" else SAFE
    align = "right" if side == "right" else "left"
    chip_h = 112
    bar_y = CHIP_BOTTOM - chip_h - 34
    im = headline(im, lines, x, bar_y - 46, maxw=maxw, align=align, size=size)
    im = bar(im, x, bar_y, align=align)
    im = chip(im, x, chip_text, align=align, bg=chip_bg)
    im = brand(im, "tl" if side == "right" else "tr")
    im.convert("RGB").save(os.path.join(OUT, "thumb-%02d.png" % idx), optimize=True)
    return im


# ------------------------------------------------------------------ 10 thumbs
build(1, "t01", [("دست‌کاری", WHT), ("عواطف", R)], "قسمت ۱ از ۳ · ۳۰ قانون پنهان",
      side="right", shift=0.20, bright=1.45, dark=0.78)

build(2, "t02", [("ذهنت را", WHT), ("می‌خوانند", R)], "۳۰ قانون پنهان قدرت",
      side="right", shift=0.16, bright=1.3, dark=0.8)

build(3, "t03", [("۶ شگرد", R), ("که شما را", WHT), ("کنترل می‌کند", WHT)], "تا آخر ببینید",
      side="left", shift=-0.16, bright=1.4, dark=0.8, maxw=620, size=118)

build(4, "t04", [("کسی نخ‌های", WHT), ("تو را می‌کشد", R)], "روان‌شناسی تاریک · فصل اول",
      side="right", shift=0.18, bright=1.35, dark=0.8)

build(5, "t05", [("چطور", WHT), ("متقاعدت", GLD), ("می‌کنند", WHT)], "فصل دوم · متقاعدسازی تاریک",
      side="left", shift=-0.20, bright=1.25, dark=0.8, maxw=600, size=124)

build(6, "t06", [("روان‌شناسی", WHT), ("تاریک", R)], "مجموعه کامل · ۳ فصل",
      side="right", shift=0.14, bright=1.25, dark=0.76, span=0.5, maxw=680, size=140)

build(7, "t07", [("کنترل ذهن", R), ("بدون اینکه", WHT), ("بفهمی", WHT)],
      "فصل سوم · کنترل نامحسوس ذهن", side="left", shift=-0.14, bright=1.4, dark=0.78, maxw=600, size=120)

build(8, "t08", [("لبخندش", WHT), ("دروغ است", R)], "نشانه‌هایی که نادیده می‌گیرید",
      side="left", shift=-0.14, bright=1.3, dark=0.78, maxw=600, size=130)

build(9, "t09", [("همه‌چیز را", WHT), ("می‌بینند", R)], "مراقب باش چه کسی گوش می‌دهد",
      side="right", bright=1.4, dark=0.76, span=0.55, maxw=620)

build(10, "t10", [("این کتاب", WHT), ("ممنوع است", R)], "خلاصه‌ی کامل · ۳ فصل",
      side="left", shift=-0.12, bright=1.3, dark=0.76, maxw=560, size=134)

# ------------------------------------------------------------------ contact sheet
ims = [Image.open(os.path.join(OUT, "thumb-%02d.png" % i)).convert("RGB") for i in range(1, 11)]
tw_, th_ = 512, 288
sheet = Image.new("RGB", (tw_ * 2 + 36, th_ * 5 + 72), (14, 15, 20))
for i, im in enumerate(ims):
    r, c = divmod(i, 2)
    sheet.paste(im.resize((tw_, th_), Image.LANCZOS), (12 + c * (tw_ + 12), 12 + r * (th_ + 12)))
sheet.save(os.path.join(OUT, "contact-sheet-thumbs.jpg"), quality=88)
print("thumbnails:", len(ims))
