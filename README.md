# youtube-files

ساختار پوشه‌بندی پروژه.

## ساختار

```
youtube-files/
├── README.md
└── tools/              # پوشه اصلی ابزار
    ├── images/         # همه تصاویر (png, jpg, svg, ...)
    ├── scripts/        # اسکریپت‌ها (py, sh, js, ...)
    └── data/           # فایل‌های داده و خروجی‌ها (json, csv, txt, ...)
```

## قواعد نام‌گذاری

- هر تصویر جدید در `tools/images/` و هر اسکریپت در `tools/scripts/` کپی/ساخته می‌شود.
- فایل‌های موقت یا خروجی اجرای اسکریپت‌ها در `tools/data/` قرار می‌گیرند.
- نام فایل‌ها با حروف کوچک و خط تیره: `my-script.sh` و `channel-thumb.png`.

## استفاده

```bash
# اجرای یک اسکریپت
bash tools/scripts/<script-name>.sh
```
