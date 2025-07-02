# Railway AI Agent 部署
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制应用代码
COPY --from=lks0426/ai-agent-ai-service:latest /app /app

# 安装依赖
RUN pip install fastapi uvicorn[standard] openai pinecone-client

# Railway 端口配置
ENV PORT=8001
EXPOSE 8001

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]