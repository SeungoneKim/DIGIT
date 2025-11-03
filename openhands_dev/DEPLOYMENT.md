# OpenHands Paper Reviewer - Deployment Guide

This guide covers different deployment options for the OpenHands Paper Reviewer.

## Quick Start

### Option 1: Local Development Setup

1. **Install OpenHands** (follow official OpenHands installation guide)

2. **Start OpenHands API server**:
```bash
# In your OpenHands installation directory
python -m openhands.server.listen --port 3000
```

3. **Run the paper reviewer**:
```bash
cd openhands_dev
pip install -r requirements.txt
python paper_reviewer.py --paper-file example_paper_data.json
```

### Option 2: Docker Compose (Recommended)

1. **Set up environment**:
```bash
# Create .env file
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

2. **Start services**:
```bash
docker-compose up -d openhands-api
# Wait for health check to pass
docker-compose --profile review up paper-reviewer
```

### Option 3: Standalone Installation

```bash
pip install -e .
openhands-review-paper --paper-file your_paper.json
```

## Production Deployment

### Docker Swarm

```yaml
# docker-stack.yml
version: '3.8'
services:
  openhands-api:
    image: ghcr.io/all-hands-ai/openhands:latest
    ports:
      - "3000:3000"
    environment:
      - ANTHROPIC_API_KEY_FILE=/run/secrets/anthropic_api_key
    secrets:
      - anthropic_api_key
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

secrets:
  anthropic_api_key:
    external: true
```

Deploy with:
```bash
docker stack deploy -c docker-stack.yml paper-review-stack
```

### Kubernetes

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openhands-paper-reviewer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: openhands-paper-reviewer
  template:
    metadata:
      labels:
        app: openhands-paper-reviewer
    spec:
      containers:
      - name: openhands-api
        image: ghcr.io/all-hands-ai/openhands:latest
        ports:
        - containerPort: 3000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: anthropic-api-key
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: openhands-service
spec:
  selector:
    app: openhands-paper-reviewer
  ports:
  - port: 3000
    targetPort: 3000
  type: LoadBalancer
```

## Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional
OPENHANDS_API_URL=http://localhost:3000
OPENHANDS_MAX_ITERATIONS=100
OPENHANDS_TIMEOUT=3600
LOG_LEVEL=INFO
```

### Configuration File

Create `config.yaml`:
```yaml
api:
  port: 3000
  host: "0.0.0.0"
  
agent:
  model: "anthropic/claude-3-5-sonnet-20241022"
  max_iterations: 100
  
paper_review:
  max_critical_items: 10
  require_evidence: true
  enable_code_analysis: true
```

## Scaling

### Horizontal Scaling

For high-volume paper review:

```bash
# Run multiple reviewer instances
for i in {1..5}; do
  python paper_reviewer.py \
    --paper-file papers/paper_$i.json \
    --output-dir reviews/review_$i &
done
wait
```

### Batch Processing

```bash
# Process multiple papers
python batch_reviewer.py \
  --papers-dir ./papers \
  --max-concurrent 3 \
  --output-dir ./batch_reviews
```

## Monitoring

### Health Checks

```bash
# Check API health
curl http://localhost:3000/api/health

# Check reviewer status
python -c "
import asyncio
from paper_reviewer import OpenHandsPaperReviewer
async def check():
    async with OpenHandsPaperReviewer() as reviewer:
        status = await reviewer.get_session_status('test')
        print(status)
asyncio.run(check())
"
```

### Logging

Configure structured logging:
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('paper_review.log'),
        logging.StreamHandler()
    ]
)
```

## Security

### API Key Management

```bash
# Use environment files
echo "ANTHROPIC_API_KEY=sk-..." > .env.local
source .env.local

# Or use secret management
kubectl create secret generic api-keys \
  --from-literal=anthropic-api-key=sk-...
```

### Network Security

```yaml
# docker-compose.yml with network isolation
networks:
  paper-review-network:
    driver: bridge
    internal: true

services:
  openhands-api:
    networks:
      - paper-review-network
```

## Troubleshooting

### Common Issues

1. **Connection refused**:
```bash
# Check if OpenHands is running
curl -f http://localhost:3000/api/health || echo "OpenHands not running"
```

2. **Memory issues**:
```bash
# Increase Docker memory limits
docker run --memory=8g --memory-swap=16g ...
```

3. **Timeout errors**:
```python
# Increase timeout in code
reviewer = OpenHandsPaperReviewer(timeout=7200)  # 2 hours
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python paper_reviewer.py --paper-file paper.json
```

### Performance Tuning

```yaml
# config.yaml
resources:
  max_memory: "8GB"
  max_cpu_time: 7200
  max_concurrent_sessions: 5

agent:
  max_iterations: 150
  timeout: 3600
```

## Backup and Recovery

### Data Backup

```bash
# Backup review results
tar -czf reviews_backup_$(date +%Y%m%d).tar.gz ./review_outputs/

# Backup configuration
cp config.yaml config_backup_$(date +%Y%m%d).yaml
```

### Session Recovery

```python
# Recover failed session
async with OpenHandsPaperReviewer() as reviewer:
    messages = await reviewer.get_session_messages(failed_session_id)
    # Process recovered data
```

## Updates and Maintenance

### Update OpenHands

```bash
# Pull latest OpenHands image
docker pull ghcr.io/all-hands-ai/openhands:latest

# Restart services
docker-compose down && docker-compose up -d
```

### Update Reviewer Code

```bash
git pull origin main
pip install -e . --upgrade
```

## Support

For deployment issues:
1. Check OpenHands documentation
2. Review logs in `./logs/` directory
3. Test with minimal example first
4. Check resource usage and limits