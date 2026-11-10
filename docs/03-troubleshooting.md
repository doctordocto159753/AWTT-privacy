# دفترچه عیب‌یابی — خطاهای واقعی مسیر

[خانه](../README.md) | [نصب](02-step-by-step.md) | [تست](05-test-plan.md)

> این صفحه خطاهایی را که در اجرای نمونه واقعی مشاهده شد از تشخیص و راه‌حل جدا می‌کند. پیام‌های واقعی بدون IP عمومی، نام کاربری خصوصی و شناسه‌های حساس بازنویسی شده‌اند. مواردی که فقط یک علت محتمل دارند، با «احتمال» مشخص شده‌اند.

## ۱. مسیر PowerShell را داخل Bash اجرا کردم

**علامت:**

~~~text
:USERPROFILE\.ssh\id_ed25519_claude.pub: No such file or directory
~~~

**علت تأییدشده:** دستور PowerShell با متغیر $env:USERPROFILE داخل Bash سرور اجرا شده بود. سرور به فایل کلید خصوصی یا عمومی Windows دسترسی ندارد.

**رفع:** پنجره PowerShell **محلی لپ‌تاپ** باز کنید و فایل public key را با Get-Content بخوانید. فقط متن فایل .pub را در authorized_keys کاربر Linux بگذارید. به سرور private key منتقل نکنید.

## ۲. هنوز authorized_keys وجود نداشت

**علامت:**

~~~text
chown: cannot access .../.ssh/authorized_keys: No such file or directory
~~~

**علت:** هیچ کلید عمومی با موفقیت به فایل مقصد اضافه نشده بود. ساخت پوشه .ssh به‌تنهایی این فایل را نمی‌سازد.

**رفع:**

~~~bash
sudo install -d -m 700 -o claude-runner -g claude-runner /home/claude-runner/.ssh
sudo nano /home/claude-runner/.ssh/authorized_keys
sudo chown -R claude-runner:claude-runner /home/claude-runner/.ssh
sudo chmod 700 /home/claude-runner/.ssh
sudo chmod 600 /home/claude-runner/.ssh/authorized_keys
~~~

متن یک‌خطی ssh-ed25519 از فایل .pub را در nano قرار دهید.

## ۳. VPS_IP به‌عنوان نام واقعی استفاده شده بود

**علامت:**

~~~text
Could not resolve hostname vps_ip
~~~

**علت:** مقدار نمونه YOUR_VPS_PUBLIC_IP یا VPS_IP هنوز با آدرس واقعی جایگزین نشده بود.

**رفع:** در SSH Config مقدار HostName را با IP/دامنه واقعی سرور خودتان جایگزین کنید؛ **آن آدرس را در ریپوی عمومی ننویسید**.

## ۴. SSH در PowerShell درست بود؛ VS Code پسورد می‌خواست

**علت محتمل:** VS Code تنظیمات SSH متفاوتی می‌خواند، Host اشتباه انتخاب شده، یا کلید خصوصی با نام غیراستاندارد صریح مشخص نشده بود.

**رفع:**
۱. فایل %USERPROFILE%\.ssh\config را با Host، HostName، User و IdentityFile کامل کنید.
۲. در PowerShell با همان فایل تست کنید:

~~~powershell
ssh -F "$env:USERPROFILE\.ssh\config" -o BatchMode=yes claude-vps whoami
~~~

۳. در VS Code با View → Command Palette (یا F1) میزبان **claude-vps** را انتخاب کنید.
۴. تفاوت «Enter passphrase for key» (عبارت کلید) و «user@host password» (پسورد سرور) را بررسی کنید.

## ۵. Ctrl+Shift+P واکنش نداشت

**رفع عملی:** در VS Code مسیر **View → Command Palette** یا F1 را امتحان کنید. ابزار را با PowerShell یا یک نرم‌افزار دیگر اشتباه نگیرید؛ فرمان باید در پنجره VS Code اجرا شود.

## ۶. Claude CLI کار می‌کند اما Git Status خطا دارد

**علامت:**

~~~text
pwd
/home/claude-runner
fatal: not a git repository
~~~

**علت تأییدشده:** Claude در پوشه Home اجرا شده بود، نه در پروژه. خرابی Git نبود.

**رفع:**

~~~bash
cd ~/claude-workspaces/projects/pipeline-test
git status
~~~

سپس همان پوشه را با File → Open Folder در پنجره Remote VS Code باز کنید.

## ۷. پنل Claude Code باز نمی‌شود

**علامت مشاهده‌شده:**

~~~text
command 'claude-vscode.editor.openLast' not found
~~~

**علت قطعی از روی این خط به‌تنهایی مشخص نیست.** ممکن است افزونه در Local نصب و در Remote فعال نشده باشد، Extension Host مشکل داشته باشد یا نسخه/فعال‌سازی پنل ناسازگار باشد.

**مسیر عیب‌یابی:**
- Extensions → بررسی نصب در بخش SSH و Enabled بودن آن.
- View → Command Palette → فرمان‌های Claude Code.
- Developer: Reload Window.
- View → Output → Log (Remote Extension Host) یا لاگ Claude Code.
- در اجرای مستندشده، کاربر **Claude Agent SDK را از رابط Chat در VS Code نصب کرد** و پنل فعال شد. این یک مشاهده موردی است، نه راه‌حل عمومی همه نسخه‌ها.
- **بعد از فعال‌شدن پنل، اجرا از خود Agent تست شود**: whoami / hostname / pwd / git status. انتخاب مدل Claude در Copilot لزوماً همان Claude Agent Harness نیست.

## ۸. Hook فایل می‌سازد ولی در پنل اجرا نمی‌شود

**تشخیص:**
- آیا settings.json در پروژه درست قرار دارد؟ .claude/settings.json
- آیا Session جدید پس از تغییر Hook باز شده؟
- آیا CLAUDE_PROJECT_DIR همان پوشه پروژه است؟
- آیا Python نصب است؟
- آیا در پنل واقعاً Claude Code/Claude Agent Harness اجرا می‌شود یا فقط مدل Claude در Chat دیگر؟

**تست مستقل (VPS Bash):**

~~~bash
printf '{"hook_event_name":"SessionStart","session_id":"manual","cwd":"%s"}\n' "$PWD" | python3 .claude/hooks/session.py
find .sessions -maxdepth 2 -type f
~~~

اگر تست دستی جواب می‌دهد ولی پنل نه، خطا احتمالاً در بارگذاری Hook یا Harness است، نه منطق Python.

## ۹. Git Auto Commit هیچ Commit نمی‌سازد

**دلایل عادی:**
- Branch روی main/master است، نه agent/*.
- فایل جدید خارج از مسیرهای مجاز است، مثلاً test.json در ریشه پروژه.
- تغییرات از قبل دستی Stage شده‌اند؛ Hook محافظه‌کارانه Skip می‌کند.
- فایل با .gitignore نادیده گرفته شده است.
- Git user.name/user.email تنظیم نشده.
- هیچ تغییر جدیدی وجود ندارد.

**دستورها:**

~~~bash
git branch --show-current
git status --short
git diff --cached --name-only
cat .sessions/<SESSION_ID>/manifest.json
~~~

اگر Branch هنوز Commit اولیه ندارد، Git Log ممکن است خالی باشد؛ این وضعیت قبل از اولین Checkpoint طبیعی است.

## ۱۰. پنل Syncthing سرور روی 8385 قطع شد

**تفاوت مهم:** آدرس http://127.0.0.1:8385 یک داشبورد عمومی سرور نیست؛ فقط از مسیر SSH Tunnel لپ‌تاپ به GUI محلی VPS Forward می‌شود.

**بررسی در Windows:**

~~~powershell
Test-NetConnection 127.0.0.1 -Port 8385
Test-NetConnection 127.0.0.1 -Port 22001
Get-ScheduledTask -TaskName "ClaudeMirror-SSH" | Select-Object TaskName,State
~~~

اگر Task خراب است، **ابتدا آن را Stop کنید** و تونل دستی مرحله ۷ راهنما را دوباره تست کنید؛ هم‌زمان دو تونل با پورت یکسان اجرا نکنید. اگر SSH دستی وصل و 8385 باز شد، مشکل از راه‌اندازی خودکار است نه لزوماً Syncthing روی VPS.

## ۱۱. خطای قطعی در tunnel.log: نام claude-vps پیدا نمی‌شود

**متن خطای واقعی (نام میزبان مستعار است):**

~~~text
ssh: Could not resolve hostname claude-vps: No such host is known.
~~~

**علت:** اسکریپت Scheduled Task بدون دسترسی به تعریف Host در SSH Config تلاش می‌کرد نام مستعار محلی را مثل دامنه DNS Resolve کند. این خطا پیش از احراز هویت و پیش از Forward شدن هر پورتی رخ می‌دهد.

**رفع آزموده‌شده:** در اجرای واقعی، هدف به IP واقعی سرور و کلید SSH صریح تغییر کرد و اتصال بازگشت. برای نسخه قابل انتشار، روش عمومی‌تر استفاده از **SSH Config دارای HostName واقعی** و گزینه صریح **-F** است:

~~~powershell
ssh -F "$env:USERPROFILE\.ssh\config" -o BatchMode=yes claude-vps whoami
~~~

اگر خروجی claude-runner بود، اسکریپت keep-tunnel.ps1 با همان Config باید بتواند وصل شود. اگر نشد، خطای جدید را از Log بررسی کنید.

**چرا Log اول دیده نشد؟** مسیر واقعی فایل %LOCALAPPDATA%\ClaudeMirror\tunnel.log است؛ نوشتن دوباره این مسیر پشت سر هم یک آدرس معتبر نیست. در نمونه جدید Log قبل از هر تلاش ایجاد می‌شود.

## ۱۲. Syncthing Connected است اما فایل Sync نمی‌شود

- در VPS پوشه **Send Only** باشد و در Windows **Receive Only**.
- Folder ID دو طرف یکسان و مسیر مقصد واقعاً وجود داشته باشد.
- هر دو Device آدرس tcp://127.0.0.1:22001 داشته باشند.
- فایل در .stignore نباشد؛ پوشه .git عمداً منتقل نمی‌شود.
- Windows Syncthing و SSH Tunnel هم‌زمان در حال اجرا باشند.
- وضعیت Folder واقعاً **Up to Date** شده باشد؛ Connected بودن دستگاه به‌تنهایی کافی نیست.

## منابع

[VS Code Remote SSH troubleshooting](https://code.visualstudio.com/docs/remote/troubleshooting) · [Claude Hooks](https://code.claude.com/docs/en/hooks) · [Syncthing Tunneling](https://docs.syncthing.net/users/tunneling.html) · [Syncthing Ignore](https://docs.syncthing.net/users/ignoring.html).
