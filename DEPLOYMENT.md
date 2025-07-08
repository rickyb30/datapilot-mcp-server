# 🚀 Deployment Guide

This guide covers deploying DataPilot MCP Server to various hosting platforms for public access via HTTPS.

## 📋 Prerequisites

1. **Environment Variables**: Set up all required environment variables
2. **API Security**: Configure API key for production use
3. **Database Access**: Ensure Snowflake credentials are secure

## 🌐 Hosting Options

### 1. **Railway** (Recommended)
**Best for**: Simple deployment, automatic HTTPS, great for development

**Steps**:
1. Fork/clone the repository
2. Connect to Railway: https://railway.app
3. Deploy from GitHub
4. Set environment variables in Railway dashboard
5. Deploy automatically gets HTTPS

**Environment Variables**:
```
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key
API_KEY=your_secure_api_key
PORT=8000
HOST=0.0.0.0
ENVIRONMENT=production
```

### 2. **Render** 
**Best for**: Free tier, automatic SSL, Git integration

**Steps**:
1. Go to https://render.com
2. Connect GitHub repository
3. Create new Web Service
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python -m src.web_server`
6. Add environment variables

### 3. **Fly.io**
**Best for**: Edge computing, global deployment

**Steps**:
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Initialize: `fly launch`
4. Set secrets: `fly secrets set SNOWFLAKE_ACCOUNT=your_account`
5. Deploy: `fly deploy`

### 4. **Google Cloud Run**
**Best for**: Enterprise-grade, serverless scaling

**Steps**:
1. Build container: `docker build -t datapilot .`
2. Tag for GCR: `docker tag datapilot gcr.io/PROJECT_ID/datapilot`
3. Push: `docker push gcr.io/PROJECT_ID/datapilot`
4. Deploy: `gcloud run deploy --image gcr.io/PROJECT_ID/datapilot`

### 5. **Heroku**
**Best for**: Traditional PaaS, simple deployment

**Steps**:
1. Create Heroku app: `heroku create datapilot-mcp`
2. Set buildpack: `heroku buildpacks:set heroku/python`
3. Set config vars: `heroku config:set SNOWFLAKE_ACCOUNT=your_account`
4. Deploy: `git push heroku main`

## 🔐 Security Configuration

### API Key Setup
For production, always set an API key:
```bash
# Strong API key example
API_KEY=dp_live_abc123xyz789_secure_key_here
```

### Environment Variables
**Required**:
- `SNOWFLAKE_ACCOUNT` - Your Snowflake account identifier
- `SNOWFLAKE_USER` - Snowflake username
- `SNOWFLAKE_PASSWORD` - Snowflake password  
- `OPENAI_API_KEY` - OpenAI API key
- `API_KEY` - API key for web server access

**Optional**:
- `SNOWFLAKE_WAREHOUSE` - Default warehouse
- `SNOWFLAKE_DATABASE` - Default database
- `SNOWFLAKE_SCHEMA` - Default schema
- `SNOWFLAKE_ROLE` - Default role
- `PORT` - Server port (default: 8000)
- `HOST` - Server host (default: 0.0.0.0)
- `ENVIRONMENT` - Environment (development/production)

## 🧪 Testing Deployment

### Health Check
```bash
curl https://your-deployment-url.com/health
```

### API Test
```bash
curl -H "Authorization: Bearer your_api_key" \
     https://your-deployment-url.com/info
```

### SQL Execution Test
```bash
curl -X POST \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT CURRENT_TIMESTAMP"}' \
  https://your-deployment-url.com/sql/execute
```

## 📡 API Endpoints

Once deployed, your server will expose:

- `GET /` - Server information
- `GET /health` - Health check
- `GET /info` - Server capabilities
- `GET /docs` - Interactive API documentation
- `POST /tools/{tool_name}` - Call specific MCP tool
- `POST /sql/execute` - Execute SQL queries
- `POST /sql/natural` - Natural language to SQL
- `GET /databases` - List databases
- `GET /tables/{database}` - List tables

## 🔗 Client Usage

### Python Client
```python
import requests

headers = {"Authorization": "Bearer your_api_key"}
base_url = "https://your-deployment-url.com"

# Get server info
response = requests.get(f"{base_url}/info", headers=headers)
print(response.json())

# Execute SQL
response = requests.post(
    f"{base_url}/sql/execute",
    headers=headers,
    json={"query": "SELECT COUNT(*) FROM your_table"}
)
print(response.json())
```

### JavaScript Client
```javascript
const headers = {
  'Authorization': 'Bearer your_api_key',
  'Content-Type': 'application/json'
};

// Natural language query
const response = await fetch('https://your-deployment-url.com/sql/natural', {
  method: 'POST',
  headers: headers,
  body: JSON.stringify({
    question: 'What are the top 10 customers by revenue?',
    database: 'SALES_DB'
  })
});

const result = await response.json();
console.log(result);
```

### cURL Examples
```bash
# List databases
curl -H "Authorization: Bearer your_api_key" \
     https://your-deployment-url.com/databases

# Natural language query
curl -X POST \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me sales by region", "database": "SALES_DB"}' \
  https://your-deployment-url.com/sql/natural
```

## 🚨 Production Considerations

### 1. **Rate Limiting**
Consider implementing rate limiting for production:
```python
# Add to web_server.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

### 2. **Monitoring**
- Set up health check monitoring
- Monitor API usage and costs
- Track Snowflake query performance

### 3. **Scaling**
- Use connection pooling for high traffic
- Consider caching frequently accessed data
- Monitor memory usage and scale accordingly

### 4. **Security**
- Rotate API keys regularly
- Use HTTPS only in production
- Implement proper logging and auditing
- Consider IP whitelisting for sensitive environments

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Connection Errors**: Verify Snowflake credentials
3. **API Key Issues**: Check authorization header format
4. **Port Conflicts**: Ensure PORT environment variable is set correctly

### Debug Mode
For development, set `ENVIRONMENT=development` to enable:
- Detailed error messages
- No API key requirement
- Auto-reload on code changes

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Snowflake Connector Documentation](https://docs.snowflake.com/en/user-guide/python-connector.html)
- [OpenAI API Documentation](https://platform.openai.com/docs)

## 🆘 Support

For deployment issues or questions, please:
1. Check the logs in your hosting platform
2. Review environment variable configuration
3. Test with minimal configuration first
4. Create an issue in the GitHub repository 