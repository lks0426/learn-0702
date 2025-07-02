# Railway 单镜像部署
# 直接使用 Docker Hub 上的 nginx 网关镜像
FROM lks0426/ai-agent-nginx:latest

# Railway 需要的端口环境变量
ENV PORT=80

# 暴露端口
EXPOSE 80

# 使用默认的 nginx 命令
CMD ["nginx", "-g", "daemon off;"]