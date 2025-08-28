@echo off
chcp 65001 >nul
echo ========================================
echo 开始推送代码到GitHub和Gitee
echo ========================================

:: 设置重试次数
set MAX_RETRIES=3

:: 推送到GitHub
echo.
echo [1/2] 推送到GitHub...
set RETRY_COUNT=0
:github_retry
set /a RETRY_COUNT+=1
echo 尝试第 %RETRY_COUNT% 次推送到GitHub...

git push origin main
if %ERRORLEVEL% EQU 0 (
    echo ✅ GitHub推送成功！
    goto gitee_push
) else (
    echo ❌ GitHub推送失败 (尝试 %RETRY_COUNT%/%MAX_RETRIES%)
    if %RETRY_COUNT% LSS %MAX_RETRIES% (
        echo 等待5秒后重试...
        timeout /t 5 /nobreak >nul
        goto github_retry
    ) else (
        echo ❌ GitHub推送失败，已达到最大重试次数
        goto gitee_push
    )
)

:: 推送到Gitee
:gitee_push
echo.
echo [2/2] 推送到Gitee...
set RETRY_COUNT=0
:gitee_retry
set /a RETRY_COUNT+=1
echo 尝试第 %RETRY_COUNT% 次推送到Gitee...

git push gitee main
if %ERRORLEVEL% EQU 0 (
    echo ✅ Gitee推送成功！
    goto success
) else (
    echo ❌ Gitee推送失败 (尝试 %RETRY_COUNT%/%MAX_RETRIES%)
    if %RETRY_COUNT% LSS %MAX_RETRIES% (
        echo 等待5秒后重试...
        timeout /t 5 /nobreak >nul
        goto gitee_retry
    ) else (
        echo ❌ Gitee推送失败，已达到最大重试次数
        goto end
    )
)

:success
echo.
echo ========================================
echo 🎉 所有推送完成！
echo ========================================
echo GitHub: ✅ 成功
echo Gitee:  ✅ 成功
goto end

:end
echo.
echo 按任意键退出...
pause >nul
