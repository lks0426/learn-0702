# Railway 部署 - 静态前端
FROM nginx:1.25-alpine

# 复制前端静态文件
COPY --from=lks0426/ai-agent-frontend:latest /usr/share/nginx/html /usr/share/nginx/html

# 复制 Nginx 配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Railway 需要的端口设置
ENV PORT=80
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]