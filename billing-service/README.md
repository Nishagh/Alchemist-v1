# Alchemist Billing Service

A FastAPI-based microservice for handling billing, credits, and payments in the Alchemist platform.

## Features

- **Credit Management**: Prepaid credits system with real-time balance tracking
- **Payment Processing**: Razorpay integration for Indian market payments
- **Transaction History**: Comprehensive audit trail and transaction logging
- **Usage Tracking**: Cross-service usage monitoring and billing
- **Atomic Operations**: Firestore transactions ensure data consistency
- **Authentication**: Firebase Auth integration with JWT tokens
- **Scalability**: Auto-scaling Cloud Run deployment

## Architecture

The billing service is designed as a Tier 2 integration service that:
- Provides billing APIs for all Alchemist services
- Handles payment processing independently
- Tracks usage across multiple services
- Maintains billing data consistency

## API Endpoints

### Health Checks
- `GET /api/v1/health` - Service health status
- `GET /api/v1/health/ready` - Readiness check
- `GET /api/v1/health/live` - Liveness check

### Credits Management
- `GET /api/v1/credits/balance` - Get user credit balance
- `GET /api/v1/credits/account` - Get complete credits account
- `GET /api/v1/credits/packages` - Get available credit packages
- `POST /api/v1/credits/purchase` - Create credit purchase order
- `GET /api/v1/credits/orders` - Get purchase order history

### Payments
- `POST /api/v1/payments/verify` - Verify payment completion
- `GET /api/v1/payments/status` - Get payment status

### Transactions
- `GET /api/v1/transactions` - Get transaction history
- `GET /api/v1/transactions/usage` - Get usage summary

### Webhooks
- `POST /api/v1/webhooks/razorpay` - Razorpay payment webhooks

## Installation

### Prerequisites
- Python 3.11+
- Docker
- Google Cloud SDK
- Firebase project setup

### Local Development

1. Clone the repository and navigate to billing-service:
```bash
cd billing-service
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Add Firebase credentials:
```bash
# Place your firebase-credentials.json in the root directory
```

6. Run the service:
```bash
python main.py
```

The service will be available at `http://localhost:8080`

### Docker Development

1. Build the Docker image:
```bash
docker build -t billing-service .
```

2. Run with environment variables:
```bash
docker run -p 8080:8080 \
  -e FIREBASE_PROJECT_ID=your-project-id \
  -e RAZORPAY_KEY_ID=your-key-id \
  -e RAZORPAY_KEY_SECRET=your-key-secret \
  billing-service
```

## Deployment

### Google Cloud Run

1. Make sure you're authenticated with Google Cloud:
```bash
gcloud auth login
gcloud config set project alchemist-e69bb
```

2. Deploy using the provided script:
```bash
./deploy.sh
```

### Cloud Build

For automated deployments, use Cloud Build:
```bash
gcloud builds submit --config cloudbuild.yaml
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `HOST` | Service host | `0.0.0.0` |
| `PORT` | Service port | `8080` |
| `FIREBASE_PROJECT_ID` | Firebase project ID | `alchemist-e69bb` |
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase credentials | `./firebase-credentials.json` |
| `RAZORPAY_KEY_ID` | Razorpay API key ID | Required |
| `RAZORPAY_KEY_SECRET` | Razorpay API key secret | Required |
| `RAZORPAY_WEBHOOK_SECRET` | Razorpay webhook secret | Required |
| `JWT_SECRET_KEY` | JWT signing secret | Required |
| `LOG_LEVEL` | Logging level | `INFO` |

### Credit System Configuration

- **Minimum Purchase**: ₹100
- **Maximum Purchase**: ₹50,000
- **GST Rate**: 18%
- **Default Low Balance Threshold**: ₹50

### Bonus Credit Tiers

- ₹500+: 10% bonus credits
- ₹1000+: 15% bonus credits
- ₹2000+: 20% bonus credits
- ₹5000+: 25% bonus credits

## Database Schema

### Firestore Collections

#### `user_credits`
User credit accounts with balance and settings.

#### `credit_transactions`
All credit transactions (purchases, usage, refunds).

#### `credit_packages`
Available credit packages for purchase.

#### `credit_orders`
Purchase orders and payment tracking.

## Testing

### Unit Tests
```bash
pytest tests/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Load Testing
```bash
# Using your preferred load testing tool
# Test endpoints with authentication headers
```

## Monitoring

### Health Checks
- Service automatically reports health status
- Kubernetes/Cloud Run health checks configured
- Firestore connectivity verification

### Logging
- Structured logging with correlation IDs
- Error tracking and alerting
- Performance metrics

### Metrics
- Request/response metrics
- Credit usage patterns
- Payment success rates
- Error rates and latency

## Security

### Authentication
- Firebase Auth integration
- JWT token validation
- User context extraction

### Authorization
- User-scoped operations
- Admin permission checks
- Rate limiting

### Data Protection
- Encrypted data transmission
- Secure payment processing
- PII data handling compliance

## Development Guidelines

### Code Style
- Follow PEP 8 standards
- Use type hints
- Write comprehensive docstrings
- Add unit tests for all functions

### Error Handling
- Use structured error responses
- Log errors with context
- Implement proper HTTP status codes
- Provide user-friendly error messages

### API Design
- RESTful endpoints
- Consistent response formats
- Proper HTTP methods
- Version your APIs

## Support

For issues and questions:
1. Check the logs: `gcloud run services logs read billing-service --region us-central1`
2. Verify health endpoints
3. Check Firebase configuration
4. Validate environment variables

## License

Part of the Alchemist platform - Internal use only.