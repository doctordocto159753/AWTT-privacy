# AWTT Privacy — محیط توسعه ریموت، نسخه‌بندی خودکار و Mirror محلی

> راهنمای فارسی و قابل اجرا برای ساخت محیط **VPS-first**: اجرای ابزار توسعه روی سرور شخصی، کار با VS Code روی لپ‌تاپ، ثبت Session و Git Checkpoint، و دریافت خودکار فایل‌ها روی Windows؛ بدون باز کردن پورت عمومی اضافه.

**وضعیت:** نمونه آموزشی / MVP تأییدشده در یک آزمایش عملی (نوامبر ۲۰۲۶). این مخزن محصول Anthropic، Microsoft یا Syncthing نیست.

> [!IMPORTANT]
> **این پروژه راهکاری برای حریم خصوصی و مدیریت مستقل فایل‌هاست، نه راهی برای تضمین جلوگیری از بن شدن یا دور زدن قوانین دسترسی جغرافیایی.** موقعیت فیزیکی کاربر، شرایط حساب و قوانین هر سرویس مستقل از محل اجرای CLI هستند. قبل از استفاده از هر سرویس، [سیاست مناطق پشتیبانی‌شده Anthropic](https://www.anthropic.com/legal/supported-regions) و مقررات مربوط را بررسی کنید. VPN یا VPS وضعیت مجاز بودن استفاده را تغییر نمی‌دهد.

## این پایپلاین چه می‌کند؟

```text
Windows laptop
  ├── VS Code → Remote SSH ───────────────────┐
  ├── Syncthing (Receive Only) ◄──────────────┼── SSH Tunnel (localhost only)
  └── ClaudeMirror/                            │
                                             ▼
Linux VPS [کاربر محدود]
  ├── VS Code Server + Claude Code
  ├── claude-workspaces/projects/<project>
  ├── .claude/hooks/session.py
  │    ├── SessionStart / UserPromptSubmit → events.jsonl
  │    └── Stop → Git checkpoint + manifest.json
  └── Syncthing (Send Only) ───────────────────┘
```

**منبع اصلی کار VPS است.** لپ‌تاپ فایل‌ها را به‌صورت یک‌طرفه دریافت می‌کند؛ پوشه `.git` مستقیماً با Syncthing منتقل نمی‌شود. در نسخه فعلی Git Bundle یا سیستم ارکستریشن جدا اضافه نکرده‌ایم.

## از کجا شروع کنم؟

| نیاز | صفحه |
|---|---|
| تصویر کلی و ارتباط مفاهیم | [نقشه دانش](docs/00-knowledge-map.md) |
| تصمیم‌های معماری، مرزها و محدودیت‌ها | [معماری](docs/01-architecture.md) |
| راه‌اندازی صفر تا صد روی Linux و Windows | [راهنمای گام‌به‌گام](docs/02-step-by-step.md) |
| خطاهای واقعی مسیر و روش تشخیص | [عیب‌یابی](docs/03-troubleshooting.md) |
| روایت تصمیم‌ها و مسیر اجرای موفق | [مطالعه موردی](docs/06-case-study.md) |
| مدل تهدید، ایمنی و حریم خصوصی | [امنیت و محدودیت‌ها](docs/04-security.md) |
| چک‌لیست آزمایش عملی | [تست پذیرش](docs/05-test-plan.md) |
| کد نمونه Hook | [session.py](examples/project-template/.claude/hooks/session.py) |
| تنظیمات Hook | [settings.json](examples/project-template/.claude/settings.json) |
| قرارداد کوتاه Session | [CLAUDE.md](examples/project-template/CLAUDE.md) |
| تونل با بازیابی خودکار | [keep-tunnel.ps1](examples/windows/keep-tunnel.ps1) |

## راه‌اندازی سریع (پس از آماده بودن SSH)

۱. از لپ‌تاپ با کلید SSH و کاربر محدود به VPS متصل شوید.
۲. در VS Code به **Remote-SSH: Connect to Host** وصل شوید؛ پروژه را از مسیر **روی VPS** باز کنید.
۳. Claude Code را روی میزبان ریموت راه بیندازید و اجرای `whoami; hostname; pwd` را از **خود پنل** بررسی کنید.
۴. نمونه `examples/project-template` را به یک مخزن Git آزمایشی منتقل و Hookها را در Session جدید تست کنید.
۵. Syncthing را روی VPS به‌صورت **Send Only** و روی Windows به‌صورت **Receive Only** راه بیندازید؛ فقط از طریق تونل SSH.
۶. ساخت `artifacts/mirror-test.txt` روی VPS را امتحان کنید و دریافت خودکار فایل روی Windows را تأیید کنید.

**راهنمای کامل، دستورات و پیش‌شرط‌های ایمنی:** [docs/02-step-by-step.md](docs/02-step-by-step.md).

## مسیر نمونه‌ها

```text
examples/
├── project-template/
│   ├── CLAUDE.md
│   ├── .gitignore
│   ├── .claude/
│   │   ├── settings.json
│   │   └── hooks/session.py
│   └── artifacts/.gitkeep
├── sync/.stignore.example
└── windows/
    ├── keep-tunnel.ps1
    └── register-task.ps1
tests/
└── test_session.py
```

نمونه `session.py` یک **بازسازی آموزشی و ایمن‌شده** از پایپلاین آزمایش‌شده است، نه فایل استخراج‌شده از سرور خصوصی. حتماً در مخزن آزمایشی خودتان با `python3 -m unittest discover -s tests -v` تست کنید. Checkpoint فقط در شاخه‌های `agent/*` و برای مسیرهای مجاز انجام می‌شود؛ هیچ `push` خودکاری وجود ندارد.

## چه چیزهایی را ادعا نمی‌کنیم؟

- «محل واقعی من برای همه سرویس‌ها مخفی است» — اثبات نشده؛ سایت می‌تواند سیگنال‌های دیگری داشته باشد.
- «حساب Claude سفید/غیرقابل‌بن است» — چنین نتیجه‌ای از تست IP، Timezone یا Browser Fingerprint به دست نمی‌آید.
- «Syncthing یک بکاپ تغییرناپذیر است» — نه؛ حذف فایل می‌تواند تکثیر شود. Versioning و بکاپ مستقل مهم‌اند.
- «همه نسخه‌های VS Code Chat و Claude Code یک Hook یکسان دارند» — خیر؛ Harness را باید آزمایش کرد.

## منابع رسمی

- [VS Code Remote SSH](https://code.visualstudio.com/docs/remote/ssh)
- [Claude Code — Hooks](https://code.claude.com/docs/en/hooks)
- [Claude Code — Setup](https://code.claude.com/docs/en/setup)
- [Syncthing — SSH Tunneling](https://docs.syncthing.net/users/tunneling.html)
- [Syncthing — Folder Types](https://docs.syncthing.net/users/foldertypes.html)
- [Syncthing — Ignore Patterns](https://docs.syncthing.net/users/ignoring.html)
- [Anthropic — Supported Regions](https://www.anthropic.com/legal/supported-regions)

## مشارکت

اگر روی نسخه‌ای از VS Code، Claude Code یا Syncthing مراحل متفاوت بود، Issue با **نسخه ابزار، سیستم‌عامل و متن خطای پاک‌سازی‌شده** ثبت کنید. هیچ IP خصوصی، SSH Key، Token، Session Transcript یا فایل حاوی اطلاعات شخصی را عمومی نکنید.

**تاریخ تدوین:** ۲۰ آبان ۱۴۰۵ / ۱۰ نوامبر ۲۰۲۶.
