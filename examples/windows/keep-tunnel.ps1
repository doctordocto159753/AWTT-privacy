# AWTT Windows reconnecting SSH tunnel.
# Run as the Windows user who owns SSH keys; no VPS changes required.
# Prerequisite: Host claude-vps is defined in %USERPROFILE%\.ssh\config.
# Test first: ssh -F "$env:USERPROFILE\.ssh\config" -o BatchMode=yes claude-vps whoami
$ErrorActionPreference = "Stop"
$ssh = Join-Path $env:WINDIR "System32\OpenSSH\ssh.exe"
$config = Join-Path $env:USERPROFILE ".ssh\config"
$log = Join-Path $PSScriptRoot "tunnel.log"

if (-not (Test-Path -LiteralPath $ssh)) { throw "Windows OpenSSH client not found: $ssh" }
if (-not (Test-Path -LiteralPath $config)) { throw "SSH config not found: $config" }

$argsSSH = @(
  "-F", $config, "-N", "-T",
  "-o", "BatchMode=yes",
  "-o", "IdentitiesOnly=yes",
  "-o", "ExitOnForwardFailure=yes",
  "-o", "ServerAliveInterval=30",
  "-o", "ServerAliveCountMax=3",
  "-o", "ConnectTimeout=10",
  "-L", "127.0.0.1:22001:127.0.0.1:22000",
  "-R", "127.0.0.1:22001:127.0.0.1:22000",
  "-L", "127.0.0.1:8385:127.0.0.1:8384",
  "claude-vps"
)

while ($true) {
  # Cap log growth during repeated network/DNS failures.
  if ((Test-Path $log) -and ((Get-Item $log).Length -gt 2MB)) {
    Move-Item -Force $log "$log.old"
  }
  Add-Content -Path $log -Value "[$(Get-Date -Format o)] Starting SSH tunnel"
  try {
    & $ssh @argsSSH 2>&1 | ForEach-Object {
      Add-Content -Path $log -Value $_.ToString()
    }
    $exitCode = $LASTEXITCODE
    Add-Content -Path $log -Value "[$(Get-Date -Format o)] SSH exited with $exitCode"
  } catch {
    Add-Content -Path $log -Value "[$(Get-Date -Format o)] Error: $_"
  }
  Start-Sleep -Seconds 10
}
