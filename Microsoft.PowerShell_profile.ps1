# PowerShell配置文件
# 设置中文编码和Git别名

# 设置控制台编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

# 设置PowerShell编码
$OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

# 设置Git别名
Set-Alias -Name g -Value git
Set-Alias -Name gs -Value "git status"
Set-Alias -Name ga -Value "git add"
Set-Alias -Name gc -Value "git commit"
Set-Alias -Name gp -Value "git push"
Set-Alias -Name gl -Value "git pull"
Set-Alias -Name gco -Value "git checkout"
Set-Alias -Name gb -Value "git branch"

# 自定义函数
function Get-GitStatus {
    git status
}

function Update-GitRepo {
    Write-Host "正在更新Git仓库..." -ForegroundColor Green
    git fetch origin
    git pull origin $(git branch --show-current)
}

function Show-GitLog {
    git log --oneline --graph --decorate -10
}

# 设置提示符
function prompt {
    $gitBranch = git branch --show-current 2>$null
    if ($gitBranch) {
        $gitBranch = " [$gitBranch]"
    }
    
    $currentPath = (Get-Location).Path
    $user = $env:USERNAME
    $computer = $env:COMPUTERNAME
    
    Write-Host "$user@$computer" -ForegroundColor Green -NoNewline
    Write-Host " " -NoNewline
    Write-Host "$currentPath" -ForegroundColor Blue -NoNewline
    Write-Host "$gitBranch" -ForegroundColor Yellow -NoNewline
    Write-Host ">" -ForegroundColor White -NoNewline
    
    return " "
}

# 显示欢迎信息
Write-Host "PowerShell配置文件已加载！" -ForegroundColor Green
Write-Host "可用的Git别名：" -ForegroundColor Yellow
Write-Host "  gs = git status" -ForegroundColor White
Write-Host "  ga = git add" -ForegroundColor White
Write-Host "  gc = git commit" -ForegroundColor White
Write-Host "  gp = git push" -ForegroundColor White
Write-Host "  gl = git pull" -ForegroundColor White
Write-Host "  gco = git checkout" -ForegroundColor White
Write-Host "  gb = git branch" -ForegroundColor White
Write-Host ""
