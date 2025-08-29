# Git脚本使用说明

## 文件说明

- `git_pull.bat` - 从Gitee拉取代码脚本
- `git_push.bat` - 推送代码到Gitee和GitHub脚本
- `README_GIT_SCRIPTS.md` - 本说明文档

## 使用方法

### 1. 从Gitee拉取代码

**运行方式：**
- 直接双击 `git_pull.bat` 文件
- 或在命令行中运行：`.\git_pull.bat`

**功能：**
- 自动检查Git仓库状态
- 自动配置Gitee远程仓库（首次使用）
- 从Gitee拉取最新代码
- 支持自动重试（每10秒重试一次）

**预设配置：**
- Gitee仓库地址：`https://gitee.com/itishsy/pobot.git`

### 2. 推送代码到Gitee和GitHub

**运行方式：**
- 直接双击 `git_push.bat` 文件
- 或在命令行中运行：`.\git_push.bat`

**功能：**
- 检查文件变更状态
- 自动添加所有文件到暂存区
- 提交代码（默认备注：变更文件名称）
- 推送到Gitee远程仓库
- 推送到GitHub远程仓库
- 显示操作结果和状态

**提交信息：**
- 默认：`变更文件名称`
- 支持自定义提交信息

## 远程仓库配置

**当前配置：**
- `origin` → GitHub: `https://github.com/itishsy/pobot.git`
- `gitee` → Gitee: `https://gitee.com/itishsy/pobot.git`

## 注意事项

1. **确保在Git仓库目录中运行脚本**
2. **确保已配置正确的远程仓库**
3. **推送前请确认代码变更内容**
4. **可以随时按 Ctrl+C 停止脚本**
5. **脚本会自动处理远程仓库配置**

## 常见操作流程

### 开发工作流

1. **拉取最新代码：**
   ```bash
   .\git_pull.bat
   ```

2. **进行代码修改**

3. **推送代码：**
   ```bash
   .\git_push.bat
   ```

### 手动命令

**拉取代码：**
```bash
git pull gitee main
```

**推送代码：**
```bash
git add .
git commit -m "变更文件名称"
git push gitee main
git push origin main
```

## 故障排除

### 拉取失败
- 检查网络连接
- 确认Gitee仓库地址正确
- 检查Git配置

### 推送失败
- 检查远程仓库配置
- 确认有推送权限
- 检查网络连接

## 脚本特性

- **中文支持** - 完全支持中文显示
- **智能检测** - 自动检测仓库状态和配置
- **错误处理** - 完善的错误提示和处理
- **自动重试** - 拉取失败时自动重试
- **状态显示** - 详细的操作状态和结果展示
