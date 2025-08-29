# 自动拉取代码脚本使用说明

## 文件说明

- `auto_pull.bat` - 通用自动拉取代码脚本（支持GitHub、Gitee等）
- `gitee_pull.bat` - 专门用于从Gitee拉取代码的批处理脚本
- `gitee_pull.ps1` - 专门用于从Gitee拉取代码的PowerShell脚本
- `AUTO_PULL_README.md` - 本说明文档
- `install_powershell_profile.ps1` - PowerShell配置文件安装脚本
- `Microsoft.PowerShell_profile.ps1` - PowerShell配置文件（中文编码+Git别名）
- `.vscode/settings.json` - VSCode中文编码设置

## 使用方法

### 方法1：从Gitee拉取代码（推荐）

#### 使用批处理文件
1. 直接双击 `gitee_pull.bat` 文件
2. 如果是第一次使用，脚本会提示您输入Gitee仓库地址
3. 脚本会自动添加Gitee远程仓库并开始拉取代码

#### 使用PowerShell脚本
1. 右键点击 `gitee_pull.ps1` 文件
2. 选择"使用PowerShell运行"
3. 按照提示配置Gitee仓库地址

### 方法2：通用拉取脚本

1. 直接双击 `auto_pull.bat` 文件
2. 选择要拉取的远程仓库：
   - 1: GitHub (origin)
   - 2: Gitee
   - 3: 自定义远程仓库
3. 按照提示配置相应的仓库地址

### 方法3：在命令行中运行

1. 打开命令提示符或PowerShell
2. 切换到项目目录
3. 运行命令：
   ```cmd
   gitee_pull.bat
   ```
   或
   ```cmd
   auto_pull.bat
   ```

## 脚本功能

### Gitee专用脚本 (`gitee_pull.bat` / `gitee_pull.ps1`)
- 自动检查Git仓库状态
- 自动配置Gitee远程仓库（首次使用时）
- 每隔10秒自动尝试从Gitee拉取最新代码
- 直到拉取成功才停止
- 支持中文显示
- 可以随时按 Ctrl+C 停止脚本

### 通用拉取脚本 (`auto_pull.bat`)
- 支持多个远程仓库（GitHub、Gitee、自定义）
- 自动检查Git仓库状态
- 智能配置远程仓库
- 每隔10秒自动重试，直到成功

### PowerShell配置文件 (`Microsoft.PowerShell_profile.ps1`)
- 自动设置UTF-8中文编码
- 提供Git命令别名（gs, ga, gc, gp, gl等）
- 自定义提示符显示Git分支
- 增强的Git工作流函数

## Gitee仓库配置

### 首次使用Gitee脚本

1. 运行 `gitee_pull.bat` 或 `gitee_pull.ps1`
2. 脚本会提示您输入Gitee仓库地址
3. 格式：`https://gitee.com/用户名/仓库名.git`
4. 脚本会自动添加名为 `gitee` 的远程仓库

### 手动配置Gitee远程仓库

如果您想手动配置，可以使用以下命令：

```bash
# 添加Gitee远程仓库
git remote add gitee https://gitee.com/用户名/仓库名.git

# 查看所有远程仓库
git remote -v

# 从Gitee拉取代码
git pull gitee main
```

### 从GitHub切换到Gitee

如果您想将主要远程仓库从GitHub切换到Gitee：

```bash
# 重命名origin为github
git remote rename origin github

# 添加Gitee作为新的origin
git remote add origin https://gitee.com/用户名/仓库名.git

# 设置Gitee为默认上游分支
git branch --set-upstream-to=origin/main main
```

## 中文编码设置

### 方法1：使用PowerShell配置文件（推荐）

1. 运行安装脚本：
   ```powershell
   .\install_powershell_profile.ps1
   ```
2. 重新启动PowerShell
3. 享受中文支持和Git别名

### 方法2：手动设置VSCode

1. 确保 `.vscode/settings.json` 文件存在
2. 重启VSCode
3. 终端将自动使用UTF-8编码

### 方法3：手动设置PowerShell

在PowerShell中运行：
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

## 故障排除

### 常见错误及解决方案

#### 1. 执行策略错误
**错误信息：** "无法加载文件，因为在此系统上禁止运行脚本"
**解决方案：**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 2. Git命令执行失败
**可能原因：**
- 当前目录不是Git仓库
- Git未安装或未配置
- 网络连接问题

**解决方案：**
- 确保在正确的Git项目目录中运行
- 检查Git安装：`git --version`
- 检查网络连接

#### 3. Gitee仓库配置失败
**可能原因：**
- Gitee仓库地址格式错误
- 网络连接问题
- 权限不足

**解决方案：**
- 检查Gitee仓库地址格式
- 确认网络连接正常
- 检查GitHub和Gitee的访问权限

#### 4. 中文显示乱码
**解决方案：**
1. 运行 `install_powershell_profile.ps1` 安装配置文件
2. 重启PowerShell
3. 检查VSCode设置文件
4. 手动设置编码：
   ```powershell
   chcp 65001
   ```

## 注意事项

1. **确保在Git仓库目录中运行脚本**
2. **确保已配置正确的远程仓库**
3. **确保有网络连接**
4. **可以随时按 Ctrl+C 停止脚本**
5. **建议安装PowerShell配置文件以获得最佳体验**
6. **Gitee和GitHub的仓库内容可能不同步，请注意选择正确的源**

## 常见问题

### Q: 如何修改重试间隔时间？
A: 编辑批处理文件中的 `timeout /t 10` 这一行，将10改为您想要的秒数。

### Q: 脚本会一直运行吗？
A: 不会，脚本会在成功拉取代码后自动停止。

### Q: 如何设置中文编码？
A: 运行 `install_powershell_profile.ps1` 脚本，它会自动设置所有必要的中文编码配置。

### Q: Git别名如何使用？
A: 安装配置文件后，可以使用：
- `gs` = `git status`
- `ga` = `git add`
- `gc` = `git commit`
- `gp` = `git push`
- `gl` = `git pull`
- `gco` = `git checkout`
- `gb` = `git branch`

### Q: 如何同时使用GitHub和Gitee？
A: 可以使用不同的远程仓库名称：
- `origin` 指向GitHub
- `gitee` 指向Gitee
- 分别使用 `git pull origin main` 和 `git pull gitee main`

## 自定义配置

如果您需要修改脚本行为，可以编辑以下部分：

- 重试间隔：修改 `timeout /t 10` 中的数字
- 日志格式：修改echo语句
- 中文编码：修改PowerShell配置文件中的编码设置
- 远程仓库名称：修改脚本中的远程仓库名称

## 技术支持

如果仍然遇到问题，请：
1. 检查错误信息
2. 确认Git仓库状态
3. 检查网络连接和远程仓库访问权限
4. 运行 `install_powershell_profile.ps1` 设置中文编码
5. 检查VSCode设置文件
6. 确认Gitee仓库地址格式正确
