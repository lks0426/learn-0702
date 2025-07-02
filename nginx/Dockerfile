# Use the official Nginx image from Docker Hub
FROM nginx:1.25-alpine

# Remove the default Nginx configuration file
RUN rm /etc/nginx/conf.d/default.conf # Remove default

# Copy the PRODUCTION Nginx configuration file
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf

# Optional: If you have SSL certificates and configs to copy for production
# COPY ./ssl-prod/ /etc/nginx/ssl/ # Assuming separate SSL certs for prod
# COPY ./nginx-ssl-options.conf /etc/nginx/ssl/options-ssl-nginx.conf
# COPY ./ssl-dhparams.pem /etc/nginx/ssl/ssl-dhparams.pem

# Expose ports (80 for HTTP, 443 for HTTPS if you configure SSL)
EXPOSE 80
# EXPOSE 443

# Command to start Nginx when the container launches
# The default Nginx CMD is ["nginx", "-g", "daemon off;"] which is usually what you want.
# So, explicitly setting CMD is often not necessary unless you need to change it.
CMD ["nginx", "-g", "daemon off;"]
