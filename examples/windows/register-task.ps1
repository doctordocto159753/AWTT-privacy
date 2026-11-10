# Register AWTT tunnel at Windows user logon (not as SYSTEM).
# Copy keep-tunnel.ps1 into $env:LOCALAPPDATA\ClaudeMirror first.
$ErrorActionPreference = "Stop"
$directory = Join-Path $env:LOCALAPPDATA "ClaudeMirror"
$script = Join-Path $directory "keep-tunnel.ps1"
if (-not (Test-Path -LiteralPath $script)) {
  throw "Missing $script; copy keep-tunnel.ps1 first"
}
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$existing = Get-ScheduledTask -TaskName "ClaudeMirror-SSH" -ErrorAction SilentlyContinue
if ($existing) {
  throw "Task ClaudeMirror-SSH already exists; inspect it before changing it."
}
$arg = '-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $script + '"'
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "ClaudeMirror-SSH" -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
Start-ScheduledTask -TaskName "ClaudeMirror-SSH"
Write-Host "Registered and started ClaudeMirror-SSH"
Write-Host "Log: $directory\tunnel.log"
