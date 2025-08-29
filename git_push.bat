@echo off
chcp 65001 >nul
title 推送代码到Gitee和GitHub

echo ========================================
echo      推送代码到Gitee和GitHub脚本
echo ========================================
echo.

:check_git
echo 检查Git仓库状态...
git status >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：当前目录不是Git仓库！
    echo 请确保在正确的Git项目目录中运行此脚本。
    pause
    exit /b 1
)

echo Git仓库检查通过！
echo.

:check_remotes
echo 检查远程仓库配置...
git remote -v
echo.

:check_changes
echo 检查文件变更状态...
git status --porcelain
if %errorlevel% neq 0 (
    echo 没有检测到文件变更。
    echo 是否继续推送？(Y/N)
    set /p continue_push="请输入选择: "
    if /i not "%continue_push%"=="Y" (
        echo 操作已取消。
        pause
        exit /b 0
    )
) else (
    echo 检测到文件变更，准备提交...
)

:commit_changes
echo.
echo 准备提交代码变更...
echo 备注信息: 变更文件名称
echo.

set /p custom_message="请输入自定义提交信息 (直接回车使用默认信息): "
if "%custom_message%"=="" (
    set commit_message="变更文件名称"
) else (
    set commit_message="%custom_message%"
)

echo 使用提交信息: %commit_message%
echo.

echo 正在添加所有文件到暂存区...
git add .

echo 正在提交代码...
git commit -m %commit_message%

if %errorlevel% neq 0 (
    echo 错误：代码提交失败！
    pause
    exit /b 1
)

echo 代码提交成功！
echo.

:push_to_gitee
echo 正在推送到Gitee...
git remote get-url gitee >nul 2>&1
if %errorlevel% equ 0 (
    echo 推送到Gitee远程仓库...
    git push gitee main
    if %errorlevel% equ 0 (
        echo Gitee推送成功！
    ) else (
        echo 警告：Gitee推送失败！
    )
) else (
    echo 警告：未配置Gitee远程仓库，跳过Gitee推送
)
echo.

:push_to_github
echo 正在推送到GitHub...
git remote get-url origin >nul 2>&1
if %errorlevel% equ 0 (
    echo 推送到GitHub远程仓库...
    git push origin main
    if %errorlevel% equ 0 (
        echo GitHub推送成功！
    ) else (
        echo 警告：GitHub推送失败！
    )
) else (
    echo 警告：未配置GitHub远程仓库，跳过GitHub推送
)
echo.

:show_status
echo 当前Git状态：
git status
echo.

:show_remotes
echo 远程仓库配置：
git remote -v
echo.

:end
echo ========================================
echo        推送操作完成！
echo ========================================
echo.
echo 操作总结：
echo - 代码已提交，备注: %commit_message%
echo - 已尝试推送到Gitee和GitHub
echo.
echo 按任意键退出...
pause >nul
