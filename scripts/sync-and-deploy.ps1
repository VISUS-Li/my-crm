# Windows 一键同步 + 部署到 Ubuntu 服务器
# 用法（在 PowerShell，项目根目录）:
#   .\scripts\sync-and-deploy.ps1           # 仅同步
#   .\scripts\sync-and-deploy.ps1 -Deploy   # 同步 + 编译 + 重启
#   .\scripts\sync-and-deploy.ps1 -SetupKey # 配置 SSH 免密登录

param(
    [switch]$Deploy,
    [switch]$SetupKey
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$ConfigExample = Join-Path $PSScriptRoot "deploy.config.example.json"
$Config = Join-Path $PSScriptRoot "deploy.config.json"

if (-not (Test-Path $Config)) {
    Copy-Item $ConfigExample $Config
    Write-Host "已创建 $Config，请确认服务器地址和密码。"
}

$args = @("scripts/sync_to_server.py")
if ($SetupKey) { $args += "--setup-key" }
if ($Deploy) { $args += "--deploy" }

python @args
