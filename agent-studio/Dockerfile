# Build stage
FROM node:18-alpine as build

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy all source files
COPY . .

# Set environment variables for build
ENV REACT_APP_FIREBASE_API_KEY=AIzaSyC9MLh9IiFIcH5RJRVLJlrTXNI5s03r4AE
ENV REACT_APP_FIREBASE_AUTH_DOMAIN=alchemist-e69bb.firebaseapp.com
ENV REACT_APP_FIREBASE_PROJECT_ID=alchemist-e69bb
ENV REACT_APP_FIREBASE_STORAGE_BUCKET=alchemist-e69bb.appspot.com
ENV REACT_APP_FIREBASE_MESSAGING_SENDER_ID=103214520240448237488
ENV REACT_APP_FIREBASE_APP_ID=1:851487020021:web:527efbdbe1ded9aa2686bc

# Set service URLs for build
ENV REACT_APP_API_BASE_URL=https://alchemist-agent-engine-851487020021.us-central1.run.app
ENV REACT_APP_KNOWLEDGE_BASE_URL=https://alchemist-knowledge-vault-851487020021.us-central1.run.app
ENV REACT_APP_MCP_MANAGER_URL=https://alchemist-tool-forge-851487020021.us-central1.run.app
ENV REACT_APP_BILLING_SERVICE_URL=https://billing-service-851487020021.us-central1.run.app

# Build the React app
RUN npm run build

# Production stage - Nginx to serve static files
FROM nginx:alpine

# Copy built app from build stage to nginx html directory
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80 (nginx default)
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"] 