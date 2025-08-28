@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 🚀 智能代码推送脚本 v2.0
echo ========================================

:: 设置重试次数和等待时间
set MAX_RETRIES=3
set WAIT_TIME=5

:: 检查Git状态
echo.
echo 📋 检查Git状态...
git status --porcelain >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 错误：当前目录不是Git仓库
    goto error_exit
)

:: 检查是否有未提交的更改
git diff --quiet
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  警告：检测到未提交的更改
    echo 建议先提交更改再推送
    set /p choice="是否继续推送？(y/N): "
    if /i "!choice!" NEQ "y" (
        echo 操作已取消
        goto end
    )
)

:: 检查远程仓库配置
echo.
echo 🔍 检查远程仓库配置...
git remote get-url origin >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 错误：未配置GitHub远程仓库
    goto error_exit
)

git remote get-url gitee >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 错误：未配置Gitee远程仓库
    goto error_exit
)

echo ✅ 远程仓库配置正常

:: 推送到GitHub
echo.
echo [1/2] 🐙 推送到GitHub...
set RETRY_COUNT=0
:github_retry
set /a RETRY_COUNT+=1
echo   尝试第 !RETRY_COUNT! 次推送到GitHub...

git push origin main
if !ERRORLEVEL! EQU 0 (
    echo   ✅ GitHub推送成功！
    set GITHUB_SUCCESS=1
    goto gitee_push
) else (
    echo   ❌ GitHub推送失败 (尝试 !RETRY_COUNT!/%MAX_RETRIES%)
    if !RETRY_COUNT! LSS %MAX_RETRIES% (
        echo   等待%WAIT_TIME%秒后重试...
        timeout /t %WAIT_TIME% /nobreak >nul
        goto github_retry
    ) else (
        echo   ❌ GitHub推送失败，已达到最大重试次数
        set GITHUB_SUCCESS=0
        goto gitee_push
    )
)

:: 推送到Gitee
:gitee_push
echo.
echo [2/2] 🐉 推送到Gitee...
set RETRY_COUNT=0
:gitee_retry
set /a RETRY_COUNT+=1
echo   尝试第 !RETRY_COUNT! 次推送到Gitee...

git push gitee main
if !ERRORLEVEL! EQU 0 (
    echo   ✅ Gitee推送成功！
    set GITEE_SUCCESS=1
    goto show_results
) else (
    echo   ❌ Gitee推送失败 (尝试 !RETRY_COUNT!/%MAX_RETRIES%)
    if !RETRY_COUNT! LSS %MAX_RETRIES% (
        echo   等待%WAIT_TIME%秒后重试...
        timeout /t %WAIT_TIME% /nobreak >nul
        goto gitee_retry
    ) else (
        echo   ❌ Gitee推送失败，已达到最大重试次数
        set GITEE_SUCCESS=0
        goto show_results
    )
)

:: 显示推送结果
:show_results
echo.
echo ========================================
echo 📊 推送结果汇总
echo ========================================
if !GITHUB_SUCCESS! EQU 1 (
    echo GitHub: ✅ 成功
) else (
    echo GitHub: ❌ 失败
)
if !GITEE_SUCCESS! EQU 1 (
    echo Gitee:  ✅ 成功
) else (
    echo Gitee:  ❌ 失败
)

if !GITHUB_SUCCESS! EQU 1 if !GITEE_SUCCESS! EQU 1 (
    echo.
    echo 🎉 所有推送完成！
    goto end
) else (
    echo.
    echo ⚠️  部分推送失败，请检查网络连接和仓库权限
    goto end
)

:error_exit
echo.
echo ❌ 脚本执行失败
echo 请检查Git配置和网络连接
goto end

:end
echo.
echo 按任意键退出...
pause >nul
