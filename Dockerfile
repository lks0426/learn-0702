# Railway 后端部署
FROM lks0426/ai-agent-backend:latest

# 切换到 root 用户安装依赖
USER root
RUN pip install gunicorn uvicorn[standard]

# 切换回原用户
USER appuser

# Railway 端口配置
ENV PORT=8000
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]