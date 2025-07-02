
技术架构
服务组件

前端服务: React.js单页应用，简洁的聊天界面
后端API: Python/FastAPI，RESTful API设计
AI Agent服务: Python + OpenAI API，处理智能对话
向量数据库: Pinecone云服务，AI语义搜索
关系数据库: PostgreSQL，存储用户和对话历史
缓存层: Redis，会话管理和性能优化
网关代理: Nginx，反向代理和静态文件服务

AWS服务架构

EC2: t3.medium实例，运行Docker容器
RDS PostgreSQL: db.t3.micro，托管数据库
ElastiCache Redis: cache.t3.micro，托管缓存
Application Load Balancer: 健康检查和负载均衡
ECR: Docker镜像仓库
VPC + Security Groups: 网络安全配置
Route53 + Certificate Manager: 域名和SSL（可选）

项目结构要求
ai-agent-project/
├── frontend/                 # React前端
├── backend/                  # FastAPI后端
├── ai-agent/                 # AI Agent服务
├── nginx/                    # Nginx配置
├── docker-compose.yml        # 本地开发环境
├── docker-compose.prod.yml   # 生产环境配置
├── aws/                      # AWS部署脚本和配置
├── docs/                     # 项目文档
├── .env.example              # 环境变量模板
└── README.md                 # 项目说明
功能需求
AI Agent核心功能

智能对话: 基于OpenAI GPT模型的对话功能
语义搜索: 使用Pinecone进行向量搜索
记忆管理: 短期记忆(Redis)和长期记忆(PostgreSQL)
多轮对话: 支持上下文连续对话

Web界面功能

聊天界面: 类似ChatGPT的简洁界面
历史记录: 查看对话历史
用户管理: 简单的用户注册登录

代码实现要求
后端API (FastAPI)

用户认证 (JWT)
对话管理接口
历史记录接口
健康检查接口
异步处理
错误处理和日志

AI Agent服务

OpenAI API集成
Pinecone向量数据库集成
对话上下文管理
流式响应支持
错误重试机制

前端应用 (React)

响应式聊天界面
实时消息显示
用户认证界面
历史对话展示
WebSocket连接

数据库设计

用户表 (users)
对话表 (conversations)
消息表 (messages)
简单的表关系设计

Docker配置要求
本地开发环境

热重载支持
开发工具集成
快速启动命令

生产环境

多阶段构建优化
安全配置
资源限制
健康检查

AWS部署要求
基础设施配置

VPC和子网配置
Security Groups安全规则
RDS和ElastiCache配置
EC2实例配置

部署脚本

自动化部署脚本
环境变量管理
SSL证书配置
域名解析设置

监控和日志

基本的健康监控
应用日志收集
错误报警配置

文档要求
README.md 包含

项目介绍和架构图
快速开始指南
本地开发环境搭建
AWS部署步骤
环境变量说明
常见问题解答

部署文档

AWS资源创建步骤
域名和SSL配置
监控设置
备份和恢复策略

安全要求

API密钥安全管理
数据库连接加密
HTTPS强制重定向
CORS跨域配置
输入验证和过滤

成本控制

使用AWS免费层资源
合理的实例规格选择
资源自动停止脚本
成本监控告警

输出要求
请提供：

完整的项目代码文件
详细的README文档
步骤清晰的部署指南
环境配置文件
简单的架构图说明

确保每个文件都有清晰的注释，让初学者能够快速理解项目结构和实现逻辑。
