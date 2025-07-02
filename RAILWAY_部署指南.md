# 🚂 Railway 部署指南

## 🎯 概述

Railway 是一个现代化的云平台，支持一键部署 Docker 应用。每月提供 $5 的免费额度，非常适合个人项目和演示。

## 🚀 快速部署步骤

### 1. 注册 Railway 账号

访问 https://railway.app/ 并使用 GitHub 账号登录。

### 2. 创建新项目

在 Railway Dashboard 中：
1. 点击 "New Project"
2. 选择 "Deploy from GitHub repo"
3. 连接你的 GitHub 仓库

### 3. 配置环境变量

在 Railway 项目设置中添加以下环境变量：

```bash
# 必需的环境变量
OPENAI_API_KEY=你的OpenAI密钥
SECRET_KEY=生成一个随机密钥
POSTGRES_PASSWORD=设置一个安全密码

# 可选的环境变量
POSTGRES_USER=user
POSTGRES_DB=ai_agent_db
```

### 4. 部署配置

Railway 会自动检测到 `railway.json` 配置文件并使用 Docker Compose 部署。

## 🔧 使用 Railway CLI（可选）

### 安装 CLI
```bash
npm install -g @railway/cli
```

### 登录
```bash
railway login
```

### 链接项目
```bash
railway link
```

### 部署
```bash
railway up
```

### 查看日志
```bash
railway logs
```

## 🌐 访问你的应用

部署成功后，Railway 会自动分配一个域名：
- 格式：`你的项目名.railway.app`
- 例如：`ai-agent-lks.railway.app`

## 📊 监控和管理

### 查看资源使用
- 在 Railway Dashboard 查看 CPU、内存、网络使用情况
- 每月 $5 免费额度通常包括：
  - 500 小时的执行时间
  - 100GB 的网络流量
  - 1GB 的内存

### 日志查看
```bash
# 使用 CLI
railway logs

# 或在 Dashboard 中查看
```

### 环境变量管理
```bash
# 添加环境变量
railway variables set KEY=value

# 查看所有环境变量
railway variables
```

## 🔄 持续部署

Railway 支持自动部署：
1. 推送代码到 GitHub
2. Railway 自动检测更改
3. 自动重新部署

## ⚠️ 注意事项

1. **数据持久化**
   - Railway 的免费套餐有存储限制
   - 建议使用外部数据库服务（如 Neon.tech）

2. **休眠策略**
   - 免费套餐的应用在无活动时可能会休眠
   - 首次访问可能需要等待唤醒

3. **资源限制**
   - 注意监控资源使用
   - 避免超出免费额度

## 🎯 优化建议

### 1. 使用外部数据库
考虑使用免费的 PostgreSQL 服务：
- Neon.tech（推荐）
- Supabase
- ElephantSQL

### 2. 减少镜像大小
使用 Alpine 基础镜像和多阶段构建。

### 3. 配置健康检查
确保服务能够自动恢复。

## 🆘 故障排除

### 部署失败
1. 检查环境变量是否正确设置
2. 查看构建日志
3. 确认 Docker 镜像可以正常拉取

### 应用无法访问
1. 检查服务是否正常启动
2. 确认端口配置正确
3. 查看 Nginx 日志

### 数据库连接失败
1. 检查数据库服务是否运行
2. 验证连接字符串
3. 确认网络配置

## 🎉 部署成功后

1. 访问你的应用：`https://你的项目.railway.app`
2. 测试所有功能
3. 分享给朋友！

## 💡 进阶技巧

### 自定义域名
Railway 支持绑定自定义域名：
1. 在项目设置中添加域名
2. 配置 DNS CNAME 记录
3. 等待 SSL 证书生成

### 多环境部署
创建多个 Railway 项目：
- `ai-agent-dev.railway.app`（开发环境）
- `ai-agent-prod.railway.app`（生产环境）

### 团队协作
Railway 支持团队功能，可以邀请其他人协作。