# PowerShell配置文件安装脚本
# 用于设置中文编码和Git别名

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   PowerShell配置文件安装程序" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查PowerShell版本
$psVersion = $PSVersionTable.PSVersion
Write-Host "当前PowerShell版本: $psVersion" -ForegroundColor Green

# 确定配置文件路径
$profilePath = $PROFILE
Write-Host "配置文件路径: $profilePath" -ForegroundColor Yellow

# 检查配置文件是否存在
if (Test-Path $profilePath) {
    Write-Host "检测到现有配置文件，将创建备份..." -ForegroundColor Yellow
    $backupPath = "$profilePath.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item $profilePath $backupPath
    Write-Host "备份已创建: $backupPath" -ForegroundColor Green
}

# 创建配置文件目录（如果不存在）
$profileDir = Split-Path $profilePath -Parent
if (!(Test-Path $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    Write-Host "已创建配置文件目录: $profileDir" -ForegroundColor Green
}

# 复制配置文件
$currentScript = $MyInvocation.MyCommand.Path
$currentDir = Split-Path $currentScript -Parent
$profileSource = Join-Path $currentDir "Microsoft.PowerShell_profile.ps1"

if (Test-Path $profileSource) {
    Copy-Item $profileSource $profilePath -Force
    Write-Host "配置文件已安装到: $profilePath" -ForegroundColor Green
} else {
    Write-Host "错误：未找到源配置文件！" -ForegroundColor Red
    exit 1
}

# 设置执行策略
Write-Host ""
Write-Host "正在设置PowerShell执行策略..." -ForegroundColor Yellow
try {
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    Write-Host "执行策略已设置为 RemoteSigned" -ForegroundColor Green
} catch {
    Write-Host "警告：无法设置执行策略，可能需要管理员权限" -ForegroundColor Yellow
}

# 测试配置文件
Write-Host ""
Write-Host "正在测试配置文件..." -ForegroundColor Yellow
try {
    . $profilePath
    Write-Host "配置文件加载成功！" -ForegroundColor Green
} catch {
    Write-Host "警告：配置文件加载时出现错误: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "现在您可以：" -ForegroundColor White
Write-Host "1. 重新启动PowerShell以应用所有设置" -ForegroundColor White
Write-Host "2. 使用Git别名（如 gs, ga, gc, gp, gl等）" -ForegroundColor White
Write-Host "3. 享受更好的中文支持和Git工作流" -ForegroundColor White
Write-Host ""
Write-Host "如果遇到问题，请检查：" -ForegroundColor Yellow
Write-Host "- 执行策略设置" -ForegroundColor Yellow
Write-Host "- 配置文件路径" -ForegroundColor Yellow
Write-Host "- PowerShell版本兼容性" -ForegroundColor Yellow
Write-Host ""

Read-Host "按回车键退出"
