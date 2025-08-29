@echo off
chcp 65001 >nul
title 从Gitee拉取代码

echo ========================================
echo        从Gitee拉取代码脚本
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

:check_gitee_remote
echo 检查Gitee远程仓库配置...
git remote get-url gitee >nul 2>&1
if %errorlevel% neq 0 (
    echo 未找到Gitee远程仓库，正在添加...
    echo.
    echo 预设Gitee仓库地址: https://gitee.com/itishsy/pobot.git
    echo.
    set /p confirm="是否使用预设地址？(Y/N，默认Y): "
    if /i "%confirm%"=="N" (
        set /p gitee_url="请输入Gitee仓库地址: "
        if "%gitee_url%"=="" (
            set gitee_url=https://gitee.com/itishsy/pobot.git
            echo 使用预设地址: %gitee_url%
        )
    ) else (
        set gitee_url=https://gitee.com/itishsy/pobot.git
        echo 使用预设地址: %gitee_url%
    )
    
    echo.
    echo 正在添加Gitee远程仓库...
    git remote add gitee %gitee_url%
    if %errorlevel% neq 0 (
        echo 错误：添加Gitee远程仓库失败！
        pause
        exit /b 1
    )
    echo Gitee远程仓库添加成功！
) else (
    echo Gitee远程仓库已配置
    git remote get-url gitee
)

echo.
echo 开始从Gitee拉取代码...
echo.

:loop
echo 正在尝试拉取代码...
git pull gitee main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo        从Gitee拉取代码成功！
    echo ========================================
    echo.
    goto :end
) else (
    echo.
    echo 拉取失败，10秒后重试...
    echo 按 Ctrl+C 可以随时停止脚本
    echo.
    timeout /t 10 /nobreak >nul
    echo.
    goto :loop
)

:end
echo 脚本执行完成！
echo 按任意键退出...
pause >nul
