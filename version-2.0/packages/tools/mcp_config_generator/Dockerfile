# Build stage
FROM golang:1.20-alpine AS builder

# Install necessary packages
RUN apk add --no-cache git ca-certificates

# Set working directory
WORKDIR /app

# Copy go mod files
COPY mcp_config_generator/go.mod mcp_config_generator/go.sum ./

# Copy the openapi-to-mcpserver directory
COPY mcp_config_generator/openapi-to-mcpserver/ ./openapi-to-mcpserver/

# Download dependencies
RUN go mod download

# Copy source code
COPY mcp_config_generator/main.go ./

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o converter .

# Final stage
FROM alpine:latest

# Install ca-certificates for HTTPS requests
RUN apk --no-cache add ca-certificates

# Set working directory
WORKDIR /root/

# Copy the binary from builder stage
COPY --from=builder /app/converter .

# Expose port
EXPOSE 8080

# Set environment variable for production
ENV PORT=8080

# Run the binary
CMD ["./converter"] 