# ABC CORE RUNTIME v0.4.0 — CROSS-DOMAIN

این نسخه تغییرات تحلیل حرفه‌ای، Multi-View Capture، Strategy-before-Recommendation، Custom Direction Composition و Visual Integrity را از Demo مردانه خارج کرده و در **Core مشترک ABC** پیاده می‌کند.

## دامنه‌های فعلی Canonical

- Hair / Haircut / Hairstyle
- Hair Color
- Makeup
- Nails
- Men's Hair & Beard
- Bridal / Complete Look coordination
- Hair Extensions — controlled
- Chemical Smoothing / Keratin — controlled
- Controlled variants defined by `CTRL-001…010`

`Skincare / Facials / Waxing` و سرویس‌های خارج از Service Ontology فعلی هنوز Canonical نیستند و این Runtime برایشان ID یا قابلیت ساختگی ایجاد نمی‌کند.

## قانون اصلی v0.4

```text
Service Resolution
→ Professional Multi-View Capture
→ AG-03 Analysis
→ Shared + Specialist Analysis Brief
→ Strategy Before Recommendation
→ Explicit Analysis Review
→ AG-04 Custom Recommendation
→ Preview
→ QA
→ Specialist Validation
```

Ranked Recommendation قبل از Analysis Review منتشر نمی‌شود.

## Multi-View Capture

UI جدید `Professional Multi-View Capture` بر اساس Service از Core می‌پرسد چه Viewهایی Required/Conditional هستند. عکس‌های `JPG / PNG / WEBP / HEIC / HEIF` پذیرفته می‌شوند. روی macOS، HEIC با `sips` داخلی سیستم Normalize می‌شود.

## اجرا روی Mac

اگر نسخه کامل را Extract کرده‌ای:

```bash
cd ~/Downloads/ABC_CORE_RUNTIME_CROSS_DOMAIN_v0.4.0
./START_ABC_LIVE_DEMO.command
```

برای استفاده از Live Provider، `.env.local` باید `OPENAI_API_KEY` معتبر داشته باشد.

اگر Upgrade Patch را روی Demo فعلی اعمال می‌کنی، Installer `.env.local` و `data/` را حفظ می‌کند.

## تست‌ها

```bash
./RUN_SMOKE_TESTS.command
```

یا:

```bash
python tests/test_integrity.py
python tests/test_cross_domain_core.py
python tests/test_preview_quarantine.py
python tests/smoke_e2e.py
```

## وضعیت

```text
CROSS_DOMAIN_CORE_IMPLEMENTED = YES
LOCAL_E2E = PASS
LIVE_PROVIDER_ALL_DOMAINS = NOT_YET_VALIDATED
PRODUCTION_READY = NO
PILOT_READY = NO
```

جزئیات معماری:

`docs/CROSS_DOMAIN_CORE_ENGINE_ARCHITECTURE_v0.4.0.md`
