# Railway 部署 - 使用修复的 Nginx 配置
FROM nginx:1.25-alpine

# 复制前端静态文件
COPY --from=lks0426/ai-agent-frontend:latest /usr/share/nginx/html /usr/share/nginx/html

# 创建正确的 Nginx 配置
RUN rm /etc/nginx/conf.d/default.conf
RUN cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # 处理 React 路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理配置（如果后端服务可用）
    location /api/v1/backend/ {
        # 暂时返回 503，因为后端服务未部署
        return 503;
    }

    location /api/v1/agent/ {
        # 暂时返回 503，因为 AI 服务未部署
        return 503;
    }

    # 健康检查
    location /health {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
EOF

# Railway 需要的端口设置
ENV PORT=80
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]