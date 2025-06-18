# Banking API Simulation Service

A mock banking API service that simulates banking data for testing and integration with the Alchemist banking customer support agent.

## Features

- Mock account balance inquiries
- Transaction history retrieval
- Fund transfers between accounts
- Customer information lookup
- API key authentication

## API Endpoints

- `GET /accounts/{account_type}/balance?customer_id={id}` - Get account balance
- `GET /accounts/{account_type}/transactions?customer_id={id}&period={period}` - Get transaction history
- `POST /transfers` - Transfer funds between accounts
- `GET /customer/info?customer_id={id}` - Get customer information
- `GET /health` - Health check endpoint

## Local Development

### Prerequisites

- Python 3.8+
- pip

### Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with the following content:
   ```
   BANKING_API_KEY=your-secret-api-key
   DEBUG=True
   ```

4. Run the application:
   ```
   python app.py
   ```

5. The API will be available at http://localhost:8080

## Docker

To build and run the Docker image locally:

```bash
docker build -t banking-api-service .
docker run -p 8080:8080 -e BANKING_API_KEY=your-secret-api-key banking-api-service
```

## Deployment to Google Cloud Run

### Prerequisites

- Google Cloud SDK installed and initialized
- Docker installed
- Google Cloud project with Cloud Run API enabled

### Steps

1. Build the Docker image:
   ```bash
   docker build -t banking-api-service .
   ```

2. Tag the image for Google Container Registry:
   ```bash
   docker tag banking-api-service gcr.io/YOUR_PROJECT_ID/banking-api-service
   ```

3. Push the image to Google Container Registry:
   ```bash
   docker push gcr.io/YOUR_PROJECT_ID/banking-api-service
   ```

4. Deploy to Cloud Run:
   ```bash
   gcloud run deploy banking-api-service \
     --image gcr.io/YOUR_PROJECT_ID/banking-api-service \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars BANKING_API_KEY=your-secret-api-key
   ```

5. After deployment, you'll receive a URL for your API service.

## Security Considerations

- This is a mock API service for demonstration purposes
- In a production environment, implement proper authentication and authorization
- Use secure environment variables for API keys
- Consider implementing rate limiting
- Add proper input validation and error handling

## Integration with Alchemist Banking Agent

After deploying to Google Cloud Run, update the API endpoints in your banking agent configuration:

```yaml
api_integrations:
  balance_inquiry:
    method: GET
    url: "https://your-cloud-run-url/accounts/{account_type}/balance"
    headers:
      Authorization: "$BANKING_API_KEY"
      Content-Type: "application/json"
    query_params:
      customer_id: "123456"
    response_template: "Your {account_type} account balance is ${balance}. Last updated on {last_updated}."
```

Replace `https://your-cloud-run-url` with the actual URL of your deployed service.

## License

MIT
