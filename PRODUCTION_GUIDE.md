# Production Hardening Guide

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/PRODUCTION_GUIDE.md
**Description:** Comprehensive guide for deploying MyRAGDB to production
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-07

---

## Table of Contents

1. [Overview](#overview)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Logging and Monitoring](#logging-and-monitoring)
4. [Error Handling and Recovery](#error-handling-and-recovery)
5. [Security Hardening](#security-hardening)
6. [Docker Deployment](#docker-deployment)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Health Monitoring](#health-monitoring)
9. [Scaling and Performance](#scaling-and-performance)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides comprehensive instructions for deploying MyRAGDB to production with proper:

- **Structured Logging**: JSON-formatted logs for machine parsing and analysis
- **Health Monitoring**: Real-time system and application health tracking
- **Error Recovery**: Automatic retry logic with exponential backoff
- **Docker Containerization**: Consistent deployment across environments
- **CI/CD Pipeline**: Automated testing and deployment
- **Security**: Request validation, rate limiting, and error handling

### Production Readiness Checklist

- [ ] All environment variables configured
- [ ] Database migrations run
- [ ] TLS certificates configured
- [ ] Log rotation enabled
- [ ] Health monitoring configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Secrets secured (API keys, encryption keys)
- [ ] Backup strategy in place
- [ ] Monitoring and alerting configured
- [ ] Runbooks prepared for common issues

---

## Infrastructure Setup

### System Requirements

**Minimum Production Setup:**
- CPU: 4 cores
- RAM: 16GB
- Storage: 100GB SSD
- Network: 1Gbps connection

**Recommended Production Setup:**
- CPU: 8+ cores
- RAM: 32GB+
- Storage: 500GB+ SSD
- Network: 10Gbps connection
- Load balancer
- Replication/failover

### Service Dependencies

MyRAGDB requires the following services:

1. **PostgreSQL 13+** - Metadata and credential storage
2. **Meilisearch 1.0+** - Keyword search indexing
3. **Chroma** - Vector search and embeddings
4. **Redis** (Optional) - Caching and session storage

### Environment Configuration

1. Copy `.env.example` to `.env.production`:

```bash
cp .env.example .env.production
```

2. Update production values:

```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:password@prod-db.example.com:5432/myragdb
DATABASE_POOL_SIZE=40

# Security
SECRET_KEY=<generated-secret-key>
AUTH_ENCRYPTION_KEY=<generated-encryption-key>

# CORS
CORS_ORIGINS=https://app.example.com

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_REQUESTS_PER_HOUR=10000
```

3. Secure the environment file:

```bash
chmod 600 .env.production
```

---

## Logging and Monitoring

### Structured Logging

MyRAGDB uses structured JSON logging for production environments. All logs are:

- **JSON formatted** for machine parsing
- **Timestamped** with ISO 8601 format
- **Context-aware** with request IDs
- **Rotated daily** to prevent disk space issues

### Initializing Logging

In your application startup:

```python
from myragdb.logging_config import LoggingConfig

# Initialize in production
LoggingConfig.initialize(
    environment='production',
    log_dir='/var/log/myragdb',
    log_level=logging.INFO,
)
```

### Log File Organization

Logs are stored in `/var/log/myragdb/`:

- `myragdb.log` - All logs (rotated every 10MB)
- `myragdb_error.log` - Errors only

### Log Aggregation

For centralized logging, configure your log aggregation service:

**CloudWatch (AWS):**
```python
import watchtower
import logging

handler = watchtower.CloudWatchLogHandler(
    log_group='/aws/myragdb/production'
)
logging.getLogger().addHandler(handler)
```

**ELK Stack (Elasticsearch, Logstash, Kibana):**
```python
import logstash
import logging

handler = logstash.TCPLogstashHandler(
    'elk.example.com',
    5000,
    version=1
)
logging.getLogger().addHandler(handler)
```

**Datadog:**
```python
from datadog import initialize, api
import logging

options = {
    'api_key': '<YOUR_API_KEY>',
    'app_key': '<YOUR_APP_KEY>',
}
initialize(**options)
```

### Log Querying Examples

**Find all errors in the last hour:**
```bash
# Using jq
cat myragdb.log | jq 'select(.level == "ERROR")'

# Using grep
grep '"level":"ERROR"' myragdb.log
```

**Find requests by request ID:**
```bash
cat myragdb.log | jq 'select(.context.request_id == "abc123")'
```

**Get error distribution:**
```bash
cat myragdb.log | jq -r '.level' | sort | uniq -c | sort -rn
```

---

## Error Handling and Recovery

### Automatic Retry Mechanism

MyRAGDB implements exponential backoff retry logic for transient failures:

```python
from myragdb.error_handling import ErrorRecoveryHandler

handler = ErrorRecoveryHandler()

# Execute with retries
result = handler.execute_with_retry(
    operation=fetch_data,
    operation_name='fetch_data',
    max_retries=3,
    retryable_exceptions=(TimeoutError, ConnectionError),
)
```

### Retry Strategy Configuration

**Exponential Backoff (Default):**
- Initial delay: 1 second
- Max delay: 60 seconds
- Multiplier: 2x

**Linear Backoff:**
```python
from myragdb.error_handling import LinearBackoffStrategy

handler = ErrorRecoveryHandler(
    retry_strategy=LinearBackoffStrategy(
        initial_delay=1.0,
        step=1.0,
    )
)
```

### Decorator Usage

```python
from myragdb.error_handling import ErrorRecoveryHandler

handler = ErrorRecoveryHandler()

@handler.retry_decorator(max_retries=3)
def risky_operation():
    # This will be retried up to 3 times
    return api.call()
```

### Error Severity Classification

Errors are automatically classified:

| Severity | Examples | Action |
|----------|----------|--------|
| LOW | NotFound, Invalid | Log and return error |
| MEDIUM | Timeout, Connection | Retry with backoff |
| HIGH | Authentication, Authorization | Log and alert |
| CRITICAL | System, Database | Alert and shutdown |

---

## Security Hardening

### Request Validation Middleware

The API includes request validation:

```python
from myragdb.api.middleware import (
    RequestValidationMiddleware,
    RequestContextMiddleware,
    RateLimitingMiddleware,
    ErrorHandlingMiddleware,
)

# Add middleware in order
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RateLimitingMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(RequestValidationMiddleware)
```

### Security Features

1. **Request Size Limits**: Max 10MB (configurable)
2. **Content-Type Validation**: Only safe types allowed
3. **CORS Protection**: Configurable origins
4. **Rate Limiting**: Per-IP and global limits
5. **Request Context**: All requests get unique IDs
6. **Error Handling**: No sensitive info in responses

### TLS/HTTPS Configuration

Use a reverse proxy (Nginx, HAProxy) for TLS:

**Nginx Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name myragdb.example.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:3002;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Secrets Management

**Store secrets securely:**

1. **Environment Variables** (development only):
```bash
export CLAUDE_API_KEY="sk-ant-..."
```

2. **AWS Secrets Manager**:
```python
import boto3

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='myragdb/prod')
api_key = json.loads(secret['SecretString'])['CLAUDE_API_KEY']
```

3. **HashiCorp Vault**:
```python
import hvac

client = hvac.Client(url='https://vault.example.com')
secret = client.secrets.kv.read_secret_version(path='myragdb/prod')
api_key = secret['data']['data']['CLAUDE_API_KEY']
```

---

## Docker Deployment

### Building the Docker Image

```bash
# Build image
docker build -t myragdb:latest .

# Tag for registry
docker tag myragdb:latest registry.example.com/myragdb:latest

# Push to registry
docker push registry.example.com/myragdb:latest
```

### Local Development with Docker

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f myragdb

# Stop services
docker-compose down
```

### Production Docker Deployment

**Using Docker Swarm:**
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml myragdb
```

**Using Kubernetes:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myragdb
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myragdb
  template:
    metadata:
      labels:
        app: myragdb
    spec:
      containers:
      - name: myragdb
        image: myragdb:latest
        ports:
        - containerPort: 3002
        env:
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 3002
          initialDelaySeconds: 10
          periodSeconds: 30
```

---

## CI/CD Pipeline

### GitHub Actions Configuration

The `.github/workflows/test.yml` pipeline automatically:

1. **Runs tests** on all Python versions (3.10, 3.11, 3.12)
2. **Lints code** with flake8, black, isort
3. **Builds Docker image**
4. **Runs integration tests** with Playwright
5. **Performs security scans** with Bandit

### Deployment Pipeline

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    needs: [test]
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          push: true
          tags: registry.example.com/myragdb:latest
          registry: registry.example.com
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}

      - name: Deploy to production
        run: |
          # Deploy using your platform
          kubectl set image deployment/myragdb myragdb=registry.example.com/myragdb:latest
```

---

## Health Monitoring

### Health Check Endpoint

The API provides a health check endpoint:

```bash
curl http://localhost:3002/api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-07T12:34:56.789000",
  "system_metrics": {
    "cpu_percent": 25.0,
    "memory_percent": 45.0,
    "disk_percent": 60.0
  },
  "components": [
    {
      "name": "database",
      "status": "healthy",
      "message": "Database connection OK"
    }
  ],
  "alerts": []
}
```

### Monitoring Integration

**Prometheus:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'myragdb'
    static_configs:
      - targets: ['localhost:3002']
    metrics_path: '/api/v1/metrics'
```

**Grafana:**
Create dashboards for:
- Request latency
- Error rates
- CPU/Memory usage
- Database connections
- Search performance

### Alerting Rules

```yaml
groups:
- name: myragdb
  interval: 30s
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    annotations:
      summary: "High error rate detected"

  - alert: HighMemoryUsage
    expr: system_memory_percent > 90
    for: 5m
    annotations:
      summary: "Memory usage above 90%"

  - alert: DatabaseUnavailable
    expr: up{job="postgres"} == 0
    for: 1m
    annotations:
      summary: "Database is unavailable"
```

---

## Scaling and Performance

### Horizontal Scaling

**Load Balancing:**
- Use round-robin load balancer
- Health check every 30 seconds
- Remove unhealthy instances

**Configuration:**
- Multiple API instances (3-5 minimum)
- Shared database backend
- Shared cache layer (Redis)

### Performance Optimization

1. **Enable Caching:**
```python
from myragdb.caching import CacheManager

cache = CacheManager(ttl_minutes=60)
```

2. **Database Connection Pooling:**
```
DATABASE_POOL_SIZE=40
DATABASE_MAX_OVERFLOW=40
```

3. **Request Compression:**
```nginx
gzip on;
gzip_types application/json text/plain;
gzip_min_length 1024;
```

### Monitoring Performance

Track these metrics:

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| API Response Time | <500ms | >1000ms |
| Search Latency | <300ms | >500ms |
| Error Rate | <0.1% | >1% |
| CPU Usage | <60% | >80% |
| Memory Usage | <70% | >85% |
| Disk Usage | <60% | >90% |

---

## Troubleshooting

### Common Issues

#### Issue: High Memory Usage

**Symptoms:** Memory exceeds 85%, slowdowns occur

**Resolution:**
1. Check log file rotation settings
2. Reduce log retention
3. Increase heap size
4. Scale horizontally

```bash
# Check memory usage
free -h

# Check process memory
ps aux | grep myragdb

# Restart service
systemctl restart myragdb
```

#### Issue: Database Connection Errors

**Symptoms:** "Connection refused" errors in logs

**Resolution:**
1. Verify PostgreSQL is running
2. Check connection string
3. Verify credentials
4. Check firewall rules

```bash
# Test database connection
psql -h localhost -U myragdb -d myragdb -c "SELECT 1;"
```

#### Issue: Search Index Corruption

**Symptoms:** Search returns no results, index errors in logs

**Resolution:**
1. Reindex using CLI command
2. Verify index files on disk
3. Check disk space

```bash
# Reindex all repositories
python -m myragdb.cli reindex

# Check index status
python -m myragdb.cli index status
```

#### Issue: High Error Rate

**Symptoms:** Error rate above threshold, alerts firing

**Resolution:**
1. Check recent deployments
2. Review error logs
3. Check external service availability
4. Rollback if necessary

```bash
# View recent errors
tail -f logs/myragdb_error.log | jq '.message'

# Count errors by type
grep '"level":"ERROR"' logs/myragdb.log | jq -r '.context.error_type' | sort | uniq -c
```

### Debugging Commands

```bash
# View application logs in JSON format
cat logs/myragdb.log | jq '.'

# Find logs for specific request
cat logs/myragdb.log | jq 'select(.context.request_id == "abc123")'

# Check system health
curl http://localhost:3002/api/v1/health | jq '.'

# Monitor resource usage
docker stats myragdb

# Check database connections
psql -h localhost -U myragdb -d myragdb -c "SELECT count(*) FROM pg_stat_activity;"
```

### Support and Escalation

1. **Check logs** - Start with application logs
2. **Check health** - Verify all services are running
3. **Check metrics** - Look for performance issues
4. **Consult runbooks** - Follow documented procedures
5. **Escalate** - Contact ops/platform team if needed

---

## References

- [Environment Variables](/.env.example)
- [Authentication Guide](/AUTHENTICATION_GUIDE.md)
- [Docker Compose](/docker-compose.yml)
- [CI/CD Pipeline](/.github/workflows/test.yml)

---

**Questions: libor@arionetworks.com**
