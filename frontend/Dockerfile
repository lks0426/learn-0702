# Stage 1: Build the React app
FROM node:18-alpine AS build

WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package.json ./
COPY package-lock.json ./
# If using yarn, uncomment below and comment out npm ci
# COPY yarn.lock ./

# Install dependencies
# RUN yarn install --frozen-lockfile
RUN npm ci

# Copy the rest of the application code
COPY . .

# Set build-time environment variables if necessary
# ARG REACT_APP_API_BASE_URL
# ENV REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL
# Note: For client-side routing with Nginx, API base URL might be relative or configured in Nginx proxy

# Build the application
RUN npm run build

# Stage 2: Serve the app with Nginx
FROM nginx:1.25-alpine

# Copy built assets from the build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy custom Nginx configuration (if any)
# We will create this nginx.conf in the nginx/ directory later,
# but for a simple CRA setup, the default Nginx config often works for serving static files.
# For client-side routing (React Router), Nginx needs to be configured to redirect all
# non-asset requests to index.html.
# COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
# Placeholder for now: use a simple config to handle React Router
RUN rm /etc/nginx/conf.d/default.conf
COPY ./nginx.default.conf /etc/nginx/conf.d/default.conf


EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
