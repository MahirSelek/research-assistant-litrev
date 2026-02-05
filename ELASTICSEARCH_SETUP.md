# Elasticsearch Serverless Setup Guide

This guide explains how to configure the app to use Elasticsearch Serverless.

## Configuration Options

The app supports two methods for configuration:

### Option 1: Streamlit Secrets (Recommended for Streamlit Cloud)

Create a `.streamlit/secrets.toml` file with the following structure:

```toml
[elasticsearch]
endpoint = "https://research-assistant-litrev-ffd9d5.es.us-central1.gcp.elastic.cloud:443"
api_key = "VXhKaElac0JKTlQxb3RnMm04SXY6ZGVnc2dhaENpd3BnZTM4U3RROHV3dw=="

[vertex_ai]
VERTEXAI_PROJECT = "literature-review-464920"
VERTEXAI_LOCATION = "us-central1"
VERTEXAI_MODEL_ID = "gemini-2.0-flash-001"

[app_config]
gcs_bucket_name = "polo-ggb-bucket"

[gcp_service_account]
type = "service_account"
project_id = "literature-review-464920"
# ... (rest of GCP credentials)
```

### Option 2: Environment Variables (For Local Development)

Set the following environment variables:

```bash
export ELASTICSEARCH_ENDPOINT="https://research-assistant-litrev-ffd9d5.es.us-central1.gcp.elastic.cloud:443"
export ELASTICSEARCH_API_KEY="VXhKaElac0JKTlQxb3RnMm04SXY6ZGVnc2dhaENpd3BnZTM4U3RROHV3dw=="
export VERTEXAI_PROJECT="literature-review-464920"
export VERTEXAI_LOCATION="us-central1"
export VERTEXAI_MODEL_ID="gemini-2.0-flash-001"
export GCS_BUCKET_NAME="polo-ggb-bucket"
export GOOGLE_APPLICATION_CREDENTIALS="/absolute/path/to/gcp_credentials.json"
```

Or create a `.env` file in the project root (the app will read environment variables automatically if you're using python-dotenv).

## Key Changes for Serverless

The app now supports **Elasticsearch Serverless** which uses:
- **Endpoint URL** + **API Key** (instead of Cloud ID + Username/Password)

The configuration automatically detects which type you're using:
- If `endpoint` and `api_key` are provided → Uses Serverless
- If `cloud_id`, `username`, and `password` are provided → Uses Hosted

## Troubleshooting

### Error: "Failed to create index 'papers': NotFoundError(404)"

This error typically occurs when:
1. The endpoint URL is incorrect
2. The API key doesn't have the right permissions
3. The Elasticsearch deployment type doesn't match (Serverless vs Hosted)

**Solution:**
- Verify your endpoint URL is correct (should end with `.es.us-central1.gcp.elastic.cloud:443` for GCP)
- Ensure your API key has permissions to create indices
- Make sure you're using Serverless configuration (endpoint + api_key) for a Serverless deployment

### Connection Issues

If you see connection errors:
1. Check that your endpoint URL is accessible
2. Verify the API key is valid and not expired
3. Ensure network/firewall allows connections to the Elasticsearch endpoint

## Testing the Connection

When you run the app, you should see in the console:
```
✓ Using Serverless Elasticsearch configuration
Connecting to Serverless Elasticsearch at: https://...
✓ Successfully connected to Elasticsearch
Index 'papers' created successfully.
```

If you see these messages, the connection is working correctly!
