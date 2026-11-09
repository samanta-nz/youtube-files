# -*- coding: utf-8 -*-
"""نسخه نهایی تامبنیل A — بهینه‌شده بر پایه اصول CTR و تایپوگرافی فارسی."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from engine import cover_crop, font, DIR

W, H = 1280, 720
BASE = os.path.dirname(os.path.abspath(__file__))
PL = os.path.join(BASE, "assets", "bg")
OUT = os.path.join(BASE, "thumbA")
os.makedirs(OUT, exist_ok=True)

R = (242, 44, 66)
RD = (148, 12, 28)
WHT = (253, 253, 255)
GLD = (246, 202, 98)

M = 56                    # right margin (grid)
BOTTOM_SAFE = H - 40      # never draw below this


# ------------------------------------------------------------------ plate
def plate(name, shift=0.11, dark=0.72, span=0.52, bright=1.3, contrast=1.12, sat=1.1):
    im = cover_crop(Image.open(os.path.join(PL, name + ".jpg")).convert("RGB"), W, H)
    if shift:
        w = int(W * (1 - shift))
        h = int(w * 9 / 16)
        x0, y0 = W - w, max(0, (H - h) // 2)
        im = im.crop((x0, y0, x0 + w, y0 + h)).resize((W, H), Image.LANCZOS)
    im = ImageEnhance.Color(im).enhance(sat)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Brightness(im).enhance(bright)
    x = np.linspace(0, 1, W)
    t = np.clip((x - (1 - span)) / span, 0, 1) ** 1.05
    m = (1 - dark) + dark * t
    a = np.asarray(im).astype(np.float32) * m[None, :, None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    # bottom breathing shade
    g = np.linspace(0, 1, H)[:, None]
    m2 = 1 - 0.28 * np.clip((g - 0.68) / 0.32, 0, 1) ** 1.3
    a = np.asarray(im).astype(np.float32) * m2[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


# ------------------------------------------------------------------ text utils
def glow(im, text, xy, f, anchor="ra", color=R, radius=26, strength=0.55):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).text(xy, text, font=f, fill=color + (215,), anchor=anchor, **DIR)
    lay = lay.filter(ImageFilter.GaussianBlur(radius))
    out = Image.alpha_composite(im, Image.composite(lay, Image.new("RGBA", im.size, (0, 0, 0, 0)),
                                                   lay.split()[3].point(lambda v: int(v * strength))))
    return out


def shadow(im, text, xy, f, anchor="ra", blur=14, alpha=235):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((xy[0] + 2, xy[1] + 10), text, font=f,
                             fill=(0, 0, 0, alpha), anchor=anchor, **DIR)
    return Image.alpha_composite(im, lay.filter(ImageFilter.GaussianBlur(blur)))


def outlined(im, text, xy, f, fill, anchor="ra", w=5):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for dx in range(-w, w + 1, 1):
        for dy in range(-w, w + 1, 1):
            if dx * dx + dy * dy <= w * w and (dx or dy):
                d.text((xy[0] + dx, xy[1] + dy), text, font=f,
                       fill=(6, 6, 10, 210), anchor=anchor, **DIR)
    im = Image.alpha_composite(im, lay)
    ImageDraw.Draw(im).text(xy, text, font=f, fill=fill, anchor=anchor, **DIR)
    return im


def line_rect(d, x_r, y, w, h, col):
    d.rectangle([x_r - w, y, x_r, y + h], fill=col)


# ------------------------------------------------------------------ build
def render_line(text, size, fill, do_glow=False, glow_strength=0.6):
    """Render one headline line with glow + shadow + outline; return tight RGBA crop."""
    w, h = W * 2, 420
    base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    f = font(size, "Black")
    origin = (w - 80, 120)

    if do_glow:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).text(origin, text, font=f, fill=R + (220,), anchor="ra", **DIR)
        g = g.filter(ImageFilter.GaussianBlur(30))
        g.putalpha(g.split()[3].point(lambda v: int(v * glow_strength)))
        base = Image.alpha_composite(base, g)

    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((origin[0] + 2, origin[1] + 10), text, font=f,
                            fill=(0, 0, 0, 235), anchor="ra", **DIR)
    base = Image.alpha_composite(base, sh.filter(ImageFilter.GaussianBlur(14)))

    ol = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(ol)
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            if dx * dx + dy * dy <= 16 and (dx or dy):
                od.text((origin[0] + dx, origin[1] + dy), text, font=f,
                        fill=(6, 6, 10, 205), anchor="ra", **DIR)
    base = Image.alpha_composite(base, ol)

    ImageDraw.Draw(base).text(origin, text, font=f, fill=fill, anchor="ra", **DIR)
    # crop to the INK box (halo/shadow excluded) so vertical rhythm stays exact
    ink = base.split()[3].point(lambda v: 255 if v > 140 else 0)
    box = ink.getbbox() or base.getbbox()
    return base.crop(box)


def build(name, lines, subtitle, meta1, meta2, payoff_boost=1.06, glow_strength=0.6):
    im = plate("t06").convert("RGBA")
    d = ImageDraw.Draw(im)

    CHIP_H = 58
    meta_y = BOTTOM_SAFE - CHIP_H
    sub_size, sub_h = 38, 54
    sub_y = meta_y - 26 - sub_h
    h_limit = sub_y - 18                     # headline bottom boundary
    gap = 6

    size = 152
    gap = 8
    top_margin = 56
    while size > 56:
        parts = [render_line(t, int(size * (payoff_boost if i == len(lines) - 1 else 1)), c,
                             do_glow=(c == R), glow_strength=glow_strength)
                 for i, (t, c) in enumerate(lines)]
        total_h = sum(p.height for p in parts) + gap * (len(parts) - 1)
        max_w = max(p.width for p in parts)
        if total_h <= (h_limit - 18) - top_margin and max_w <= W - 2 * M - 8:
            break
        size -= 2

    # optically centre the block in the text column (uniform gaps, safe margins)
    y = top_margin + max(0, ((h_limit - 18) - top_margin - total_h) // 2)
    for p in parts:
        im.alpha_composite(p, (W - M - p.width, int(y)))
        y += p.height + gap

    # subtitle + rule
    im = im.convert("RGBA")
    d = ImageDraw.Draw(im)
    fs = font(sub_size, "Bold")
    sw = d.textlength(subtitle, font=fs, **DIR)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((W - M + 2, sub_y + 8), subtitle, font=fs,
                            fill=(0, 0, 0, 210), anchor="ra", **DIR)
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(9)))
    d = ImageDraw.Draw(im)
    d.text((W - M, sub_y + 4), subtitle, font=fs, fill=GLD, anchor="ra", **DIR)
    rule_r = W - M - sw - 42
    cy = sub_y + 4 + sub_h // 2
    d.rectangle([rule_r - 116, cy - 3, rule_r, cy + 3], fill=R)

    # meta row
    f1 = font(30, "Bold")
    w1 = d.textlength(meta1, font=f1, **DIR)
    box1 = [W - M - w1 - 52, meta_y, W - M, meta_y + CHIP_H]
    d.rounded_rectangle(box1, radius=10, fill=RD)
    d.text((box1[2] - 26, meta_y + 13), meta1, font=f1, fill=WHT, anchor="ra", **DIR)

    f2 = font(27, "Medium")
    w2 = d.textlength(meta2, font=f2, **DIR)
    x2_r = box1[0] - 26
    if x2_r - w2 >= M:
        d.text((x2_r, meta_y + 16), meta2, font=f2, fill=(224, 229, 238), anchor="ra", **DIR)
    else:
        d.text((W - M, meta_y - 44), meta2, font=f2, fill=(224, 229, 238), anchor="ra", **DIR)

    # brand
    fb = font(23, "Bold")
    d.text((M - 12, 28), "روان‌شناسی تاریک", font=fb, fill=(255, 255, 255, 205), anchor="la", **DIR)
    d.line([(M - 12, 66), (M + 44, 66)], fill=R, width=4)

    im.convert("RGB").save(os.path.join(OUT, name), quality=96, subsampling=0, optimize=True)
    return im


LINES = [("شگردهایی که", WHT), ("شما را کنترل", WHT), ("می‌کنند", R)]
SUB = "و باید آگاه باشی"
BOOK = "کتاب صوتی روان‌شناسی تاریک"
PART = "مقدمه و فصل یک"

build("A1 - نهایی - شگردهایی که شما را کنترل می‌کنند.jpg", LINES, SUB, PART, BOOK,
      payoff_boost=1.06, glow_strength=0.6)
# نسخه دوم: کلمه پایانی بزرگ‌تر و هاله قوی‌تر (برای تست A/B)
build("A2 - هاله قوی‌تر.jpg", LINES, SUB, PART, BOOK, payoff_boost=1.12, glow_strength=0.9)

print("done:", os.listdir(OUT))
