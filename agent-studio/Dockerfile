FROM node:18-alpine as build

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy all source files (excluding firebase-credentials.json which will be mounted at runtime)
COPY . .

# Ensure we're not trying to use the credentials file during build
RUN rm -f firebase-credentials.json

# Set Firebase environment variables for build (from .env file)
ENV REACT_APP_FIREBASE_API_KEY=AIzaSyC9MLh9IiFIcH5RJRVLJlrTXNI5s03r4AE
ENV REACT_APP_FIREBASE_AUTH_DOMAIN=alchemist-e69bb.firebaseapp.com
ENV REACT_APP_FIREBASE_PROJECT_ID=alchemist-e69bb
ENV REACT_APP_FIREBASE_STORAGE_BUCKET=alchemist-e69bb.appspot.com
ENV REACT_APP_FIREBASE_MESSAGING_SENDER_ID=103214520240448237488
ENV REACT_APP_FIREBASE_APP_ID=1:851487020021:web:527efbdbe1ded9aa2686bc

# Build the app
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install production dependencies only
RUN npm ci --only=production

# Copy built app from the build stage
COPY --from=build /app/build ./build
COPY --from=build /app/server.js .
COPY --from=build /app/server ./server

# The Firebase credentials will be mounted at runtime from Secret Manager
# Create a placeholder directory for credentials
RUN mkdir -p /firebase

# Expose port
EXPOSE 8080

# Start the app
CMD ["npm", "run", "start:prod"] 