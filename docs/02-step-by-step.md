# نصب و اجرای گام‌به‌گام AWTT Privacy

[خانه](../README.md) | [نقشه دانش](00-knowledge-map.md) | [عیب‌یابی](03-troubleshooting.md)

> **تفاوت محیط‌ها:** بخش‌های **Windows PowerShell** روی لپ‌تاپ اجرا می‌شوند؛ بخش‌های **VPS Bash** روی سرور Linux. اگر در ترمینال عبارت root@server یا claude-runner@server می‌بینید، داخل PowerShell محلی ویندوز نیستید.

## ۰. پیش‌نیازها

- Windows، VS Code، Remote - SSH، OpenSSH Client، PowerShell و Syncthing روی لپ‌تاپ.
- یک سرور Linux (نمونه آزمایش‌شده Ubuntu / x86_64) با SSH، Git، Python 3 و فضای کافی.
- حساب و دسترسی قانونی به سرویس موردنظر؛ VPS خارجی مقررات جغرافیایی را تغییر نمی‌دهد.
- هیچ تغییری در Nginx، Xray یا پورت‌های عمومی سرویس‌های موجود لازم نیست.

**VPS Bash — فقط بررسی وضعیت:**

~~~bash
uname -m
free -h
df -h "$HOME"
command -v git
command -v python3
ss -ltn | grep -E ':22 |:8384 |:22000 |:22001 ' || true
~~~

## ۱. ساخت کاربر محدود VPS

**VPS Bash — مدیر سیستم:**

~~~bash
sudo adduser --disabled-password --gecos "" claude-runner
sudo install -d -m 700 -o claude-runner -g claude-runner /home/claude-runner/.ssh
~~~

کاربر را عضو گروه sudo نکنید؛ فقط پروژه‌های لازم را در دسترسش بگذارید.

## ۲. ساخت کلید SSH روی لپ‌تاپ

**Windows PowerShell محلی:**

~~~powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.ssh" | Out-Null
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\id_ed25519_claude" -C "awtt-vps"
Get-Content "$env:USERPROFILE\.ssh\id_ed25519_claude.pub" | Set-Clipboard
~~~

اگر این کلید را قبلاً ساخته‌اید، آن را بازنویسی نکنید. **فقط کلید عمومی با پسوند .pub را انتقال دهید.** کلید خصوصی باید روی Windows بماند.

**VPS Bash — مدیر سیستم:**

~~~bash
sudo nano /home/claude-runner/.ssh/authorized_keys
# کلید عمومی کپی‌شده را به صورت یک خط ssh-ed25519 ... Paste کنید.
sudo chown -R claude-runner:claude-runner /home/claude-runner/.ssh
sudo chmod 700 /home/claude-runner/.ssh
sudo chmod 600 /home/claude-runner/.ssh/authorized_keys
~~~

پیش از اعتماد به SSH Host، اثرانگشت کلید عمومی سرور را از یک کانال مستقل بررسی کنید.

**Windows PowerShell — فایل Config:**

~~~powershell
notepad "$env:USERPROFILE\.ssh\config"
~~~

~~~sshconfig
Host claude-vps
    HostName YOUR_VPS_PUBLIC_IP
    User claude-runner
    Port 22
    IdentityFile ~/.ssh/id_ed25519_claude
    IdentitiesOnly yes
~~~

**Windows PowerShell — تست:**

~~~powershell
ssh -F "$env:USERPROFILE\.ssh\config" claude-vps whoami
~~~

خروجی باید claude-runner باشد. درخواست Passphrase کلید خصوصی با درخواست Password حساب لینوکس متفاوت است.

## ۳. نصب Claude Code و Workspace

**VPS Bash — وارد کاربر claude-runner شوید:**

~~~bash
whoami
echo "$HOME"
curl -fsSL https://claude.ai/install.sh -o /tmp/claude-install.sh
less /tmp/claude-install.sh
bash /tmp/claude-install.sh
export PATH="$HOME/.local/bin:$PATH"
claude --version
claude doctor
~~~

نصب رسمی را با مجوز محدود و فقط در صورت داشتن دسترسی مجاز به سرویس انجام دهید. [مستندات رسمی](https://code.claude.com/docs/en/setup).

**VPS Bash — پروژه آزمایشی:**

~~~bash
mkdir -p ~/claude-workspaces/projects/pipeline-test
cd ~/claude-workspaces/projects/pipeline-test
git init -b main
git config user.name "Your Name"
git config user.email "you@example.invalid"
git switch -c agent/pipeline-test
mkdir -p artifacts docs
claude
~~~

ورود Claude روی سرور از ورود قبلی افزونه محلی Windows جداست؛ لازم نیست نسخه محلی را حذف کنید.

## ۴. VS Code Remote SSH

۱. در لپ‌تاپ افزونه [Remote - SSH](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh) را نصب کنید.
۲. از **View → Command Palette** (یا F1) گزینه **Remote-SSH: Connect to Host** را اجرا کنید؛ میزبان claude-vps را انتخاب کنید.
۳. در **File → Open Folder** این مسیر را باز کنید: /home/claude-runner/claude-workspaces/projects/pipeline-test
۴. افزونه Claude Code را در بخش **SSH — Installed** بررسی کنید، نه فقط **Local — Installed**.
۵. اگر از Chat داخلی VS Code با Claude Agent SDK استفاده می‌کنید، آن را با افزونه مستقل Anthropic یکسان فرض نکنید. Session Target / Harness و اجرای Hookها را جداگانه تست کنید.

**پرامپت تست در همان پنل Agent:**

~~~text
Run whoami, hostname, pwd, and git status.
Report results without modifying any files.
~~~

خروجی باید نام کاربر محدود، میزبان VPS و مسیر Git پروژه را نشان دهد. Git خطای «not a repository» می‌دهد اگر پنل در پوشه Home باز شده باشد.

## ۵. نصب نمونه Hook و Git Checkpoint

**VPS Bash — کد مرجع را در پوشه‌ای جدا از پروژه بگیرید:**

~~~bash
git clone https://github.com/doctordocto159753/AWTT-privacy.git ~/awtt-reference
cd ~/claude-workspaces/projects/pipeline-test
cp -a ~/awtt-reference/examples/project-template/.claude ./
cp ~/awtt-reference/examples/project-template/CLAUDE.md ./
cp ~/awtt-reference/examples/project-template/.gitignore ./
chmod 700 .claude/hooks/session.py
~~~

اسکریپت را پیش از اجرای آن بخوانید. این مثال در SessionStart و UserPromptSubmit رویداد ثبت می‌کند و در Stop تلاش به Git Checkpoint محدود دارد. فقط روی شاخه‌های agent/* و مسیرهای صریحی مانند src، docs، tests، scripts و artifacts Commit می‌کند. هیچ Git Push خودکاری ندارد.

**VPS Bash — تست دستی Hook:**

~~~bash
mkdir -p artifacts
printf '%s\n' "AWTT smoke" > artifacts/smoke.txt
printf '{"hook_event_name":"Stop","session_id":"smoke","cwd":"%s"}\n' "$PWD" | python3 .claude/hooks/session.py
cat .sessions/smoke/manifest.json
git log -1 --oneline
~~~

سپس در پنل Agent یک Session **جدید** بسازید و ایجاد فایل آزمایشی بخواهید. باید در .sessions/<id>/ فایل events.jsonl و manifest.json شکل بگیرد. تست واحد مثال:

~~~bash
cd ~/awtt-reference
python3 -m unittest discover -s tests -v
~~~

توجه: فایل root مانند test.json به‌طور پیش‌فرض Auto Commit نمی‌شود؛ باید مسیر مجاز را مطابق نیاز خودتان تنظیم کنید.

## ۶. راه‌اندازی Syncthing VPS

با راهنمای رسمی [Syncthing Downloads](https://syncthing.net/downloads/) و [Config](https://docs.syncthing.net/users/config.html) بسته سازگار با توزیع را نصب کنید.

**VPS Bash — مدیر سیستم، برای Ubuntu/Debian:**

~~~bash
sudo apt-get update
sudo apt-get install -y syncthing
syncthing --version
~~~

اگر نسخه جدید موردنیاز است، از مخزن رسمی apt.syncthing.net استفاده کنید. **قبل از Start سرویس**، کاربر claude-runner باید Config را تولید و مسیر واقعی را بررسی کند:

~~~bash
syncthing generate --no-port-probing
syncthing paths
~~~

مسیر رایج config در نسخه‌های جدید ~/.local/state/syncthing/config.xml است، اما اگر دستور paths مسیر متفاوتی نشان داد، همان معتبر است. تنظیمات زیر را **پیش از اولین اجرای دائمی** اعمال کنید:

| گزینه | مقدار |
|---|---|
| GUI Listen Address | 127.0.0.1:8384 |
| Sync Protocol Listen Addresses | tcp://127.0.0.1:22000 |
| NAT / Global Discovery / Local Discovery / Relaying | Disabled |

اگر config را در XML ویرایش می‌کنید، طبق ساختار نسخه نصب‌شده عمل کنید؛ بدون بررسی، فایل را بازنویسی نکنید.

**VPS Bash — مدیر سیستم:**

~~~bash
sudo systemctl enable --now syncthing@claude-runner.service
sudo systemctl status syncthing@claude-runner.service --no-pager
ss -ltn | grep -E ':8384 |:22000 '
~~~

فقط 127.0.0.1 باید شنونده باشد. اگر 0.0.0.0 دیدید، سرویس را متوقف و پیش از ادامه اصلاح کنید.

## ۷. Syncthing Windows و تونل SSH

Syncthing Windows را از [سایت پروژه](https://syncthing.net/downloads/) یا نصب‌کننده‌ای که در آن معرفی شده بگیرید؛ بعضی نصب‌کننده‌ها شخص ثالث هستند. در GUI محلی Windows روی http://127.0.0.1:8384 همان تنظیمات Listen/Discovery را اعمال کنید.

**Windows PowerShell — تونل دستی:**

~~~powershell
ssh -F "$env:USERPROFILE\.ssh\config" -N -T -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L 127.0.0.1:22001:127.0.0.1:22000 -R 127.0.0.1:22001:127.0.0.1:22000 -L 127.0.0.1:8385:127.0.0.1:8384 claude-vps
~~~

پنجره PowerShell را باز نگه دارید. در مرورگر لپ‌تاپ:
- http://127.0.0.1:8384 ← داشبورد Windows
- http://127.0.0.1:8385 ← داشبورد VPS از طریق SSH

در هر پنل از **Actions → Show ID** شناسه دستگاه را بگیرید و با **Add Remote Device** در دستگاه مقابل ثبت کنید. در Advanced هر Remote Device آدرس **tcp://127.0.0.1:22001** را قرار دهید. ابتدا باید هر دو **Connected** شوند. [منبع فنی رسمی](https://docs.syncthing.net/users/tunneling.html).

## ۸. فعال کردن Mirror یک‌طرفه

**VPS Bash — کاربر claude-runner:**

~~~bash
cd ~/claude-workspaces
cp ~/awtt-reference/examples/sync/.stignore.example .stignore
cat .stignore
~~~

پیش از فعال‌سازی، Ignoreهای فایل‌های حساس را بررسی کنید. در داشبورد سرور **Add Folder**:
- Label: Claude Workspaces
- Folder ID: claude-workspaces
- Path: /home/claude-runner/claude-workspaces
- Folder Type: **Send Only**
- Sharing: دستگاه Windows

در Windows درخواست Share را قبول کنید:
- Folder ID: همان claude-workspaces
- Path: D:\ClaudeMirror (یا پوشه خالی دیگری)
- Folder Type: **Receive Only**
- File Versioning: Simple Versioning، مثلاً ۵ نسخه

**VPS Bash — تست انتقال:**

~~~bash
echo "Hello from VPS" > ~/claude-workspaces/projects/pipeline-test/artifacts/mirror-test.txt
~~~

باید در Windows فایل D:\ClaudeMirror\projects\pipeline-test\artifacts\mirror-test.txt ظاهر شود، بدون اینکه scp اجرا کنید. Syncthing، .git را عمداً منتقل نمی‌کند؛ حذف روی VPS نیز می‌تواند به Mirror منتقل شود.

## ۹. خودکارسازی SSH Tunnel ویندوز

قبل از اجرای Task، تونل دستی قبلی را با Ctrl+C متوقف کنید. فایل [keep-tunnel.ps1](../examples/windows/keep-tunnel.ps1) را پس از بررسی در مسیر %LOCALAPPDATA%\ClaudeMirror\keep-tunnel.ps1 ذخیره کنید؛ سپس [register-task.ps1](../examples/windows/register-task.ps1) را بررسی و با PowerShell اجرا کنید.

**Windows PowerShell — بررسی کلید بدون Prompt:**

~~~powershell
ssh -F "$env:USERPROFILE\.ssh\config" -o BatchMode=yes claude-vps whoami
~~~

اگر کلید Passphrase دارد و Task نمی‌تواند بدون پرسش متصل شود، ssh-agent ویندوز و ssh-add را برای **همان کاربر ویندوز** تنظیم کنید. Task نمونه با نام ClaudeMirror-SSH در زمان Logon اجرا می‌شود، خودش دوباره وصل می‌شود و Log را در %LOCALAPPDATA%\ClaudeMirror\tunnel.log ثبت می‌کند. اگر Task قبلاً وجود داشته باشد، اسکریپت ثبت آن را بازنویسی نمی‌کند.

**Windows PowerShell — تست:**

~~~powershell
Get-ScheduledTask -TaskName "ClaudeMirror-SSH" | Select-Object TaskName,State
Get-ScheduledTaskInfo -TaskName "ClaudeMirror-SSH" | Select-Object LastRunTime,LastTaskResult
Test-NetConnection 127.0.0.1 -Port 8385
Test-NetConnection 127.0.0.1 -Port 22001
Get-Content "$env:LOCALAPPDATA\ClaudeMirror\tunnel.log" -Tail 20
~~~

اگر نام claude-vps Resolve نشد، فایل %USERPROFILE%\.ssh\config و مسیر صریح پارامتر -F را بررسی کنید.

## ۱۰. تست پذیرش و پایان

- پنل Agent باید نام کاربر VPS و مسیر Workspace واقعی را برگرداند.
- Hook باید Manifest بنویسد و فقط در شاخه agent/* Commit مجاز ایجاد کند.
- هر دو Syncthing باید Connected و Up to Date باشند.
- فایل آزمایشی VPS باید خودکار در Windows ظاهر شود.
- پس از قطع و بازگشت اتصال SSH، Task باید تونل را بازیابی کند.
- پورت‌های 8384 و 22000 روی اینترنت عمومی باز نباشند.

**پایان MVP همین‌جاست.** Git Bundle، GitHub Push خودکار، سرویس جدید و Pipeline پیچیده عمداً فعال نمی‌شوند.

منابع: [VS Code Remote SSH](https://code.visualstudio.com/docs/remote/ssh) · [Claude Hooks](https://code.claude.com/docs/en/hooks) · [Syncthing Folder Types](https://docs.syncthing.net/users/foldertypes.html) · [Syncthing Ignore](https://docs.syncthing.net/users/ignoring.html).
