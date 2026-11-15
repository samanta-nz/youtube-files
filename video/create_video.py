#!/usr/bin/env python3
"""Build the Paykan documentary as a 1080p narrated slideshow."""
from pathlib import Path
import math, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import arabic_reshaper
from bidi.algorithm import get_display
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "video"
ASSETS = OUT / "assets"
FRAMES = OUT / "frames"
AUDIO = ROOT / "audio/full-assembled.mp3"
W, H = 1920, 1080
BG = (7, 20, 34)
PANEL = (11, 31, 47)
GOLD = (231, 190, 105)
TEAL = (79, 183, 191)
WHITE = (240, 242, 243)
MUTED = (174, 187, 196)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def rtl(s):
    return get_display(arabic_reshaper.reshape(str(s)))

def fit_font(text, max_width, size, bold=False):
    path = BOLD if bold else FONT
    for s in range(size, 17, -1):
        f = ImageFont.truetype(path, s)
        if f.getlength(rtl(text)) <= max_width:
            return f
    return ImageFont.truetype(path, 18)

def wrap_rtl(draw, text, font, max_width):
    # Input is split by explicit phrases first; wrap on spaces while measuring shaped runs.
    lines, current = [], ""
    for word in str(text).split():
        trial = (current + " " + word).strip()
        if current and draw.textbbox((0, 0), rtl(trial), font=font)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines

def rounded(draw, box, radius=24, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

# Reconstructed shot sequence based on the editorial timeline; no invented narration timecodes.
chapters = [
("هوک", [
("پیکان؛ خاطرهٔ جاده", "یک خودرو در خاطرات خانواده‌ها", 0, "پیکان در تهران • عکس ۲۰۱۴، نه بازسازی سفر مشخص"),
("پشت نشان بریتانیایی", "هیلمن هانتر و ریشه‌های پیکان", 1, "هیلمن هانتر • عکس: تهران، ۲۰۱۴"),
("یک پرسش دربارهٔ پایان", "از آغازِ مسیر تا آخرین روز تولید", 2, "روایت بر پایهٔ منابع و تصاویر آرشیوی"),
("داستانی فراتر از یک خودرو", "صنعت، خانواده و خاطرهٔ جمعی", None, "مستند تصویری • پیکان"),
]),
("یک ماشین، دو زندگی", [
("راهی در حافظه", "پیکان به‌عنوان تصویر نمادین جاده", 0, "تصویر آرشیوی؛ نه شاهد سفر خانواده‌ای مشخص"),
("شناسنامهٔ بریتانیایی", "هیلمن هانتر و خانوادهٔ ارو", 0, "عکس خودرو در تهران • ۲۰۱۴"),
("ساخت در ایران", "ایران‌ناسیونال و تولید داخلی", 1, "تصویر پیکان در تهران • ۲۰۱۴"),
("دو نام، یک روایت", "هیلمن هانتر / پیکان دولوکس", None, "۱۳۵۱ سال مدل است؛ تصویر گرافیکی، نه عکس رونمایی"),
]),
("پشت نشان بریتانیایی", [
("برادران روتس", "شرکتی که پشت نام هیلمن ایستاد", None, "کارت گرافیکی؛ آگهی آرشیوی استفاده نشده"),
("هیلمن ایمپ", "خودروی کوچکِ ساخته‌شده در لینوود", None, "بازسازی تایپوگرافیک؛ تصویر موزه‌ای درج نشده"),
("زنجیرهٔ تأمین", "لینوود و کاونتری در شبکهٔ تولید", None, "نقشهٔ شماتیک، نه نقشهٔ تاریخی دقیق"),
("کارخانه و بازار", "هزینه، ظرفیت و تصمیم‌های تولید", None, "نمایش گرافیکی"),
]),
("ورود کرایسلر", [
("۱۹۶۴ ← ۱۹۶۷", "سرمایه‌گذاری و تغییر کنترل", None, "خط زمانی گرافیکی"),
("بحث در پارلمان", "نگرانی از آیندهٔ صنعت بریتانیا", None, "بر پایهٔ Hansard • ۱۷ ژانویهٔ ۱۹۶۷"),
("دو سوی یک قرارداد", "سرمایه، کنترل و تولید", 1, "تصویر خودرو مستقل از سند پارلمانی"),
("ادامهٔ مسیر", "روتس زیر چتر کرایسلر", None, "نمودار شماتیک"),
]),
("قرارداد ایران در پارلمان", [
("وزیر صنایع", "موضوع قرارداد در مجلس عوام", None, "Hansard • ۱۶ دسامبر ۱۹۷۵"),
("برآورد زیان", "۸۰ میلیون پوند برای بخش بریتانیایی", None, "برچسب تاریخی؛ نه کل کرایسلر آمریکا"),
("حدود ۲۵ هزار شغل", "برآورد مطرح‌شده در بحث پارلمانی", None, "منبع: Hansard • شرکت بریتانیایی"),
("قطعات تا مونتاژ", "تأمین مجموعه‌قطعات برای ایران", None, "مسیر شماتیک، نه تصویر آرشیوی"),
]),
("خروج کرایسلر از اروپا", [
("۱۹۷۸", "واگذاری کرایسلر اروپا به پژو", None, "خط زمانی بر پایهٔ سند ثبتی پژو"),
("روتس ← کرایسلر ← پژو", "تغییر مالکیت در چند گام", None, "نمودار اختصاصی"),
("نامی که باقی ماند", "اثر دورهٔ تالبوت در لینوود", None, "عکس معامله نیست؛ پلِ تالبت‌دار نمایش داده نشده"),
("پایان یک دوره", "میراث صنعتی با نامی تازه", None, "کارت گرافیکی"),
]),
("چرا پیکان ماند؟", [
("ماشینِ کار", "تاکسی و خودروی روزمره", 2, "تاکسی پیکان • تجریش، ۲۰۱۰"),
("قطعه و تعمیرکار", "آشنایی تعمیرگاه‌ها با خودرو", 0, "تصویر خودرو؛ نه عکس تعمیرگاه"),
("۹۰٬۸۶۶ سواری", "آمار تولید سال ۱۹۷۷", None, "منبع: ایرانیکا • سواری"),
("۹۸٬۰۵۱ دستگاه با وانت", "رقم کل تولید، نه رقم وانت به‌تنهایی", None, "۱۹۷۷ • مجموع سواری و وانت"),
]),
("هزینهٔ ماندگاری", [
("تولیدِ ماندگار", "زیرساخت و مهارت ساخت", 1, "نمایش تصویری پیکان؛ نه خط تولید"),
("مدلی از ۱۳۵۱", "پیکان دولوکس در یک دورهٔ طولانی", 2, "سال مدل؛ نه تاریخ عکس"),
("محصولِ بعدی", "توان جایگزینی و نوآوری", None, "کارت مفهومی"),
("چه چیزی جا ماند؟", "مهارت، شبکه و خاطره", None, "گرافیک اختصاصی"),
]),
("آخرین پیکان سواری", [
("۲۵ اردیبهشت ۱۳۸۴", "پایان تولید پیکان سواری", None, "کارت تاریخ؛ عکس واقعی مراسم در دسترس نیست"),
("یک پایان ثبت‌شده", "۱۵ مه ۲۰۰۵", None, "تاریخ مراسم؛ نه تاریخِ ساخت عکس"),
("وانت، روایتی جداگانه", "سواری و وانت را از هم جدا کنیم", 0, "عکس خودرو؛ نه عکس وانت"),
("پایان یا آغازِ خاطره؟", "چه چیزی جای پیکان را گرفت؟", 2, "تصویر آرشیوی پیکان • تهران، ۲۰۱۴"),
])]

# Segment boundaries from the supplied timeline (seconds); visual shot points within each part are evenly spread,
# and are not represented as precise narration timecodes.
segments = [(0.80,58.08),(61.08,144.52),(147.52,253.88),(256.88,335.24),(338.24,446.92),(449.92,516.68),(519.68,634.08),(637.08,731.44),(734.44,839.12)]


def photo_panel(base, path):
    if not path:
        return
    im = Image.open(path).convert("RGB")
    # Fill wide archival-photo panel without distortion.
    target = (1010, 720)
    im = ImageOps.fit(im, target, method=Image.Resampling.LANCZOS, centering=(0.5,0.5))
    # Mild cinematic tone, preserving legibility/details.
    im = Image.blend(im, Image.new("RGB", target, (8,20,26)), 0.07)
    mask = Image.new("L", target, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,target[0]-1,target[1]-1), radius=24, fill=255)
    base.paste(im, (68, 180), mask)

def render_slide(idx, chapter_num, chapter, scene, frame_path, progress):
    title, subtitle, photo_idx, caption = scene
    base = Image.new("RGB", (W,H), BG)
    d = ImageDraw.Draw(base)
    # Subtle grid and ring geometry.
    for x in range(75, W, 150): d.line((x,80,x,H-70), fill=(17,38,52), width=1)
    for y in range(130, H-70, 140): d.line((55,y,W-55,y), fill=(15,35,49), width=1)
    d.ellipse((1320,-240,1840,280), outline=(24,53,68), width=2)
    d.ellipse((1338,-222,1822,262), outline=(40,53,58), width=1)
    # Header/footer ribbons.
    d.rectangle((0,0,14,H), fill=GOLD)
    d.text((66,48), "PAYKAN  /  DOCUMENTARY", font=ImageFont.truetype(BOLD,25), fill=(183,196,205))
    d.text((W-62,47), rtl(f"{chapter_num:02d}  /  {chapter}"), font=fit_font(chapter,540,25,True), fill=GOLD, anchor="ra")

    # Photo or data-art panel on left.
    rounded(d,(54,154,1106,928),30,fill=(13,34,48),outline=(70,104,116),width=2)
    path = None
    if photo_idx is not None:
        names=["hillman-2014-front.jpg","hillman-2014-green.jpg","paykan-taxi-2010.jpg"]
        path=ASSETS/names[photo_idx]
    if path and path.exists():
        photo_panel(base,path)
        d=ImageDraw.Draw(base)
        # caption strip on photo panel
        rounded(d,(82,830,1078,894),14,fill=(9,24,37))
        d.text((1046,846),rtl(caption),font=fit_font(caption,900,22),fill=WHITE,anchor="ra")
    else:
        # Abstract graphic motif, chapter-related but clearly illustrative.
        d.ellipse((205,300,955,1050), outline=(40,79,91), width=4)
        d.ellipse((300,395,860,955), outline=(97,83,58), width=2)
        d.arc((250,345,910,1005), start=200, end=330, fill=TEAL, width=5)
        d.line((190,710,980,710), fill=(39,66,77), width=3)
        # small semantic bars/cards
        for j in range(4):
            x=245+j*192
            rounded(d,(x,580,x+142,672),14,fill=(14,48,62),outline=(47,102,112),width=2)
            d.rectangle((x+20,620,x+122,634), fill=[GOLD,TEAL,(110,139,156),(210,151,90)][j])
        d.text((1025,844),rtl(caption),font=fit_font(caption,900,22),fill=WHITE,anchor="ra")
    # Right text panel
    rounded(d,(1136,154,1866,928),30,fill=(8,23,37),outline=(42,75,90),width=2)
    d.text((1808,208),rtl("تصویر آرشیوی / گرافیک اختصاصی"),font=ImageFont.truetype(FONT,22),fill=TEAL,anchor="ra")
    title_font=fit_font(title,620,56,True)
    y=300
    for line in wrap_rtl(d,title,title_font,620):
        d.text((1808,y),rtl(line),font=title_font,fill=WHITE,anchor="ra")
        y += 86
    subfont=fit_font(subtitle,620,33)
    y=max(y+34,500)
    for line in wrap_rtl(d,subtitle,subfont,620):
        d.text((1808,y),rtl(line),font=subfont,fill=MUTED,anchor="ra")
        y += 54
    # Decorative callout label
    rounded(d,(1210,650,1808,738),16,fill=(27,39,40),outline=(106,94,61),width=1)
    d.text((1774,673),rtl(chapter),font=ImageFont.truetype(BOLD,27),fill=GOLD,anchor="ra")
    d.text((1774,710),rtl("روایت تصویری بر پایهٔ تایم‌لاین تدوین"),font=ImageFont.truetype(FONT,19),fill=MUTED,anchor="ra")
    d.text((1210,796),"Photo credit and source links in repository credits",font=ImageFont.truetype(FONT,17),fill=(161,175,183))
    # Progress line, purely visual; not a narration timestamp.
    d.rounded_rectangle((68,1005,W-68,1018),radius=7,fill=(44,64,77))
    d.rounded_rectangle((68,1005,68+int((W-136)*progress),1018),radius=7,fill=GOLD)
    d.text((W-72,1032),"ARCHIVAL DOCUMENTARY  •  1080p",font=ImageFont.truetype(FONT,17),fill=(148,166,177),anchor="ra")
    base.save(frame_path, "JPEG", quality=88, optimize=True)

def main():
    if not AUDIO.exists(): raise FileNotFoundError(AUDIO)
    ASSETS.mkdir(parents=True,exist_ok=True); FRAMES.mkdir(parents=True,exist_ok=True)
    all_scenes=[]
    for ci, (chapter, scenes) in enumerate(chapters,1):
        a,b=segments[ci-1]
        for si, scene in enumerate(scenes):
            all_scenes.append((ci,chapter,scene,a+(b-a)*si/len(scenes),a+(b-a)*(si+1)/len(scenes)))
    # Opening and ending cards cover the music-only head/tail.
    total=843.12
    slides=[]
    render_slide(0,1,"هوک",("پیکان؛ خاطرهٔ جاده","یک مستند تصویری دربارهٔ خودرویی در زندگی روزمره",None,"آغازِ روایت"),FRAMES/"slide_000.jpg",0)
    slides.append((FRAMES/"slide_000.jpg",0.8))
    for idx,(ci,chapter,scene,a,b) in enumerate(all_scenes,1):
        p=FRAMES/f"slide_{idx:03d}.jpg"
        render_slide(idx,ci,chapter,scene,p,(a+b)/(2*total))
        slides.append((p,b-a))
        if idx % 4 == 0 and idx < len(all_scenes):
            next_ci,next_chapter=all_scenes[idx][0],all_scenes[idx][1]
            tp=FRAMES/f"transition_{next_ci:02d}.jpg"
            render_slide(200+next_ci,next_ci,next_chapter,("گذار موسیقی",f"بدون گفتار • فصل بعد: {next_chapter}",None,"گذار موسیقی • بدون گفتار"),tp,(b+1.5)/total)
            slides.append((tp,3.0))
    render_slide(99,9,"پایان",("پیکان؛ خاطرهٔ جاده","پایان روایت، ادامهٔ پرسش",None,"پایانِ موسیقی"),FRAMES/"slide_099.jpg",1)
    slides.append((FRAMES/"slide_099.jpg",4.0))
    concat=FRAMES/"slides.txt"
    with concat.open("w",encoding="utf-8") as f:
        for p,dur in slides:
            f.write(f"file '{p.resolve()}'\n")
            f.write(f"duration {dur:.3f}\n")
        f.write(f"file '{slides[-1][0].resolve()}'\n")
        f.write("duration 0.040\n")
    ff=imageio_ffmpeg.get_ffmpeg_exe()
    target=OUT/"paykan-documentary-1080p.mp4"
    cmd=[ff,"-nostdin","-hide_banner","-y","-f","concat","-safe","0","-i",str(concat),"-i",str(AUDIO),"-vf","fps=30,scale=in_range=full:out_range=tv,format=yuv420p","-c:v","libx264","-preset","fast","-crf","27","-profile:v","high","-level:v","4.1","-c:a","copy","-shortest","-movflags","+faststart",str(target)]
    print(f"Rendering {len(slides)} slides against full narration…",flush=True)
    subprocess.run(cmd,check=True)
    print(f"Created {target} ({target.stat().st_size:,} bytes)")

if __name__=="__main__": main()
