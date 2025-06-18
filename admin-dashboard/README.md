# Alchemist Admin Dashboard

A comprehensive monitoring and management dashboard for the Alchemist AI platform. This internal tool provides real-time visibility into all Alchemist services, logs, metrics, and alerts.

## Features

### 🏠 **Dashboard Overview**
- Real-time service health monitoring
- System performance metrics
- Service status indicators
- Performance charts and analytics

### 🔧 **Service Status**
- Detailed service health checks
- Response time monitoring
- Service configuration details
- Quick service actions

### 📊 **Log Viewer**
- Real-time log streaming
- Advanced filtering and search
- Service-specific log views
- Log export functionality

### 📈 **Performance Metrics**
- CPU and memory usage charts
- Response time analytics
- Request volume tracking
- Error rate monitoring

### 🚨 **Alerts & Monitoring**
- Configurable alert rules
- Multi-channel notifications (Email, Slack, Webhook)
- Alert acknowledgment and resolution
- Alert history and analytics

### ⚙️ **Settings**
- Dashboard configuration
- Notification settings
- Security configuration
- API key management

## Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn

### Development Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start development server:**
   ```bash
   npm start
   ```

3. **Access the dashboard:**
   Open [http://localhost:3000](http://localhost:3000)

### Production Build

1. **Build the application:**
   ```bash
   npm run build
   ```

2. **Serve with nginx:**
   ```bash
   docker build -t alchemist-admin-dashboard .
   docker run -p 80:80 alchemist-admin-dashboard
   ```

## Service Monitoring

The dashboard monitors the following Alchemist services:

### Core Services
- **🚀 Agent Engine** - Main orchestration service
- **📚 Knowledge Vault** - Document processing & search
- **🌉 Agent Bridge** - WhatsApp Business integration

### Supporting Services
- **🚀 Agent Launcher** - Agent deployment automation
- **🔨 Tool Forge** - MCP server management
- **🎨 Agent Studio** - Web application interface

## Configuration

### Environment Variables

Create a `.env` file for development:

```env
REACT_APP_API_BASE_URL=https://your-api-domain.com
REACT_APP_REFRESH_INTERVAL=30000
REACT_APP_LOG_LEVELS=ERROR,WARN,INFO,DEBUG
```

### Service URLs

Update service URLs in `src/pages/Dashboard.js`:

```javascript
const services = [
  {
    name: 'Agent Engine',
    url: 'https://alchemist-agent-engine-your-project.run.app',
    // ...
  },
  // Add your service URLs
];
```

## Features in Detail

### 🔍 **Real-time Monitoring**
- Service health checks every 30 seconds
- Live performance metrics
- Automatic error detection
- Status change notifications

### 📱 **Responsive Design**
- Dark/Light theme support
- Mobile-friendly interface
- Responsive charts and tables
- Touch-friendly controls

### 🔐 **Security Features**
- API key authentication
- Session management
- Audit logging
- IP whitelisting

### 📧 **Alert Notifications**
- Email notifications
- Slack integration
- Custom webhooks
- SMS alerts (configurable)

## Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t alchemist-admin-dashboard .

# Run the container
docker run -d \
  --name alchemist-dashboard \
  -p 80:80 \
  alchemist-admin-dashboard
```

### Docker Compose

```yaml
version: '3.8'
services:
  admin-dashboard:
    build: .
    ports:
      - "80:80"
    environment:
      - NODE_ENV=production
    restart: unless-stopped
```

## API Integration

The dashboard integrates with Alchemist services via REST APIs:

### Health Check Endpoints
- `GET /health` - Service health status
- `GET /metrics` - Performance metrics
- `GET /logs` - Service logs

### Alert Configuration
- `POST /api/alerts/rules` - Create alert rules
- `GET /api/alerts` - Fetch active alerts
- `PUT /api/alerts/{id}/acknowledge` - Acknowledge alerts

## Customization

### Adding New Services

1. **Update service configuration:**
   ```javascript
   // src/pages/Dashboard.js
   const services = [
     // existing services...
     {
       name: 'Your New Service',
       url: 'https://your-service-url.com',
       description: 'Service description',
       icon: '🆕',
     }
   ];
   ```

2. **Add service-specific metrics:**
   ```javascript
   // src/pages/Metrics.js
   const serviceColors = {
     // existing colors...
     'Your New Service': '#your-color',
   };
   ```

### Custom Alert Rules

```javascript
// src/pages/Alerts.js
const customRule = {
  name: 'Custom Alert',
  service: 'Your Service',
  metric: 'custom_metric',
  operator: '>',
  threshold: 100,
  severity: 'warning',
};
```

## Troubleshooting

### Common Issues

1. **Services not loading:**
   - Check CORS configuration
   - Verify service URLs
   - Check network connectivity

2. **Charts not displaying:**
   - Ensure data format is correct
   - Check console for JavaScript errors
   - Verify chart dependencies

3. **Notifications not working:**
   - Check SMTP/webhook configuration
   - Verify API keys and credentials
   - Check firewall settings

### Debug Mode

Enable debug logging:
```javascript
localStorage.setItem('debug', 'alchemist:*');
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the Alchemist AI platform and is proprietary software.

## Support

For support and questions:
- Create an issue in the repository
- Contact the Alchemist development team
- Check the main Alchemist documentation

---

**Built with ❤️ for the Alchemist AI Platform**