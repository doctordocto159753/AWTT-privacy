# برنامه تست پذیرش (Acceptance Test)

[خانه](../README.md) | [راهنما](02-step-by-step.md) | [عیب‌یابی](03-troubleshooting.md)

> هر تست یک گزاره قابل مشاهده دارد. «مجاز بودن حساب نزد ارائه‌دهنده مدل» جزو معیارهای این تست نیست و از نتایج فنی قابل استخراج نیست.

## ماتریس تست

| ID | تست | نحوه بررسی | معیار قبولی |
|---|---|---|---|
| T01 | SSH با کلید | Windows: ssh -F ... claude-vps whoami | نام کاربر محدود بدون Password سرور |
| T02 | محیط اجرای پنل Claude | Agent: whoami, hostname, pwd, git status | نام VPS و مسیر مخزن پروژه |
| T03 | SessionStart / UserPromptSubmit | .sessions/<id>/events.jsonl | ثبت رویداد؛ بدون متن کامل پرامپت |
| T04 | Stop / Manifest | .sessions/<id>/manifest.json | وضعیت آخرین نوبت و Git |
| T05 | Auto Checkpoint | Branch agent/* و فایل artifacts | Git Commit با فایل مجاز |
| T06 | حفاظت از main | همان تست روی main | بدون Commit خودکار |
| T07 | حفاظت از Stage | قبل از Stop یک فایل را Stage کنید | Commit خودکار Skip شود |
| T08 | فایل حساس | ساخت .env در پروژه آزمایشی | وارد Git Commit نشود |
| T09 | Syncthing دستگاه‌ها | هر دو GUI | Connected |
| T10 | Mirror | ساخت artifacts/mirror-test.txt روی VPS | ظاهرشدن همان فایل روی Windows |
| T11 | قطع اینترنت لپ‌تاپ | ایجاد فایل روی VPS در حالت آفلاین | دریافت بعد از بازگشت اتصال |
| T12 | پایداری تونل | قطع صرفاً پردازش SSH Tunnel | بازگشت پورت 8385 بدون دخالت دستی |
| T13 | عدم در معرض بودن پورت | VPS: ss -ltn | 8384 و 22000 فقط روی 127.0.0.1 |
| T14 | Archive versioning | ویرایش/حذف فایل آزمایشی | امکان مشاهده نسخه پیشین در Versioning مقصد |

## دستورات تست سریع

**VPS Bash:**

~~~bash
cd ~/claude-workspaces/projects/pipeline-test
whoami; hostname; pwd; git branch --show-current
python3 ~/awtt-reference/examples/project-template/.claude/hooks/session.py </dev/null
git log -3 --oneline
find .sessions -maxdepth 2 -type f
ss -ltn | grep -E ':8384 |:22000 '
~~~

توجه: اجرای مستقیم Hook بدون JSON ورودی طبیعی است که چیزی نسازد؛ برای تست واقعی JSON رخداد بفرستید یا Session جدید Claude باز کنید.

**Windows PowerShell:**

~~~powershell
ssh -F "$env:USERPROFILE\.ssh\config" -o BatchMode=yes claude-vps whoami
Test-NetConnection 127.0.0.1 -Port 8385
Test-NetConnection 127.0.0.1 -Port 22001
Get-ScheduledTask -TaskName "ClaudeMirror-SSH" | Select-Object TaskName, State
Get-Content "$env:LOCALAPPDATA\ClaudeMirror\tunnel.log" -Tail 20
~~~

**تست خودکار نمونه Hook (محلی یا VPS، روی clone همین ریپو):**

~~~bash
python3 -m unittest discover -s tests -v
~~~

این تست‌ها با Git Repoهای موقت کار می‌کنند و به Repo واقعی کاربر Push نمی‌زنند.

## تست دستی تغییر و Sync

**VPS Bash:**

~~~bash
mkdir -p ~/claude-workspaces/projects/pipeline-test/artifacts
date -u +%FT%TZ > ~/claude-workspaces/projects/pipeline-test/artifacts/acceptance.txt
~~~

**Windows:** وجود فایل ClaudeMirror/projects/pipeline-test/artifacts/acceptance.txt و مقدار همان زمان را بررسی کنید. سپس فایل را در VPS ویرایش کنید و به‌روزرسانی Windows را مشاهده کنید.

## آنچه معیار قبولی نیست

- Coverage 100%، Network Trust Score یا Browser Fingerprint Score به‌معنای «غیرقابل ردیابی بودن» نیست.
- یک IP خروجی آلمانی اثبات نمی‌کند کاربر از نظر جغرافیایی مجاز است.
- WebRTC «No Leak» به‌تنهایی تست DNS، GPS یا تمام مسیرهای برنامه نیست.
- فایل روی لپ‌تاپ بدون Verify شدن Git Commit به معنی Checkpoint کامل نیست.
- Connected بودن دو دستگاه، Up to Date بودن همه پوشه‌ها را تضمین نمی‌کند.

## نتیجه ثبت‌شده از اجرای واقعی

طبق تأییدهای صاحب آزمایش: اجرای Claude روی VPS، Hookها، Git Checkpoint، دریافت فایل Mirror و بازیابی اتصال خودکار SSH موفق بوده‌اند. **نمونه‌کد عمومی جدید** ممکن است تفاوت‌هایی با نسخه شخصی استفاده‌شده در آن اجرا داشته باشد؛ به همین دلیل باید تست واحد بالا و تست دستی روی محیط خودتان نیز انجام شود.

منابع: [Claude Hooks](https://code.claude.com/docs/en/hooks) · [Syncthing Folder Types](https://docs.syncthing.net/users/foldertypes.html).
