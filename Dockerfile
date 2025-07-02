# Railway 后端部署
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制应用代码
COPY --from=lks0426/ai-agent-backend:latest /app /app

# 安装依赖
RUN pip install fastapi uvicorn[standard] python-jose[cryptography] passlib[bcrypt] python-multipart sqlalchemy psycopg2-binary redis

# Railway 端口配置
ENV PORT=8000
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]