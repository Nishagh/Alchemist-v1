FROM node:18-alpine as build

# Set working directory
WORKDIR /app

# Copy package files
COPY admin-dashboard/package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY admin-dashboard/ .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy custom nginx config
COPY admin-dashboard/nginx.conf /etc/nginx/nginx.conf

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]