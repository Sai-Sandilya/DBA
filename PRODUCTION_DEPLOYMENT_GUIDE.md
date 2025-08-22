# 🚀 DBA-GPT Production Deployment Guide

## Overview
This guide will help you deploy your DBA-GPT system to production with enterprise-grade security, monitoring, and scalability.

## 🎯 Pre-Production Checklist

### 1. Security Review
- [ ] All API keys and secrets are environment variables
- [ ] Database connections use SSL/TLS
- [ ] Authentication system implemented
- [ ] Rate limiting configured
- [ ] CORS policies set
- [ ] Input validation implemented

### 2. Performance Testing
- [ ] Load testing completed
- [ ] Database connection pooling optimized
- [ ] Query timeouts configured
- [ ] Memory usage optimized
- [ ] Response times meet SLA requirements

### 3. Monitoring Setup
- [ ] Logging configured
- [ ] Metrics collection enabled
- [ ] Alerting rules defined
- [ ] Health checks implemented
- [ ] Backup procedures tested

## 🐳 Docker Deployment

### Create Production Dockerfile
```dockerfile
# Dockerfile.production
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 dbaapp && chown -R dbaapp:dbaapp /app
USER dbaapp

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Start application
CMD ["streamlit", "run", "core/web/interface.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Build and Run
```bash
# Build production image
docker build -f Dockerfile.production -t dba-gpt:production .

# Run with environment variables
docker run -d \
  --name dba-gpt-prod \
  -p 8501:8501 \
  -e DBA_ENV=production \
  -e MYSQL_HOST=your-mysql-host \
  -e MYSQL_DATABASE=your-database \
  -e MYSQL_USERNAME=your-username \
  -e MYSQL_PASSWORD=your-password \
  -e JWT_SECRET=your-jwt-secret \
  -v /var/log/dba-gpt:/app/logs \
  dba-gpt:production
```

## ☸️ Kubernetes Deployment

### Create Namespace
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dba-gpt
  labels:
    name: dba-gpt
```

### Create ConfigMap
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dba-gpt-config
  namespace: dba-gpt
data:
  config.yaml: |
    environment: "production"
    debug: false
    # Add your configuration here
```

### Create Secret
```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: dba-gpt-secrets
  namespace: dba-gpt
type: Opaque
data:
  mysql-password: <base64-encoded-password>
  jwt-secret: <base64-encoded-jwt-secret>
  openai-api-key: <base64-encoded-api-key>
```

### Create Deployment
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dba-gpt
  namespace: dba-gpt
  labels:
    app: dba-gpt
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dba-gpt
  template:
    metadata:
      labels:
        app: dba-gpt
    spec:
      containers:
      - name: dba-gpt
        image: your-registry/dba-gpt:production
        ports:
        - containerPort: 8501
        env:
        - name: DBA_ENV
          value: "production"
        - name: MYSQL_HOST
          valueFrom:
            configMapKeyRef:
              name: dba-gpt-config
              key: mysql-host
        - name: MYSQL_PASSWORD
          valueFrom:
            secretKeyRef:
              name: dba-gpt-secrets
              key: mysql-password
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: logs
        persistentVolumeClaim:
          claimName: dba-gpt-logs-pvc
```

### Create Service
```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: dba-gpt-service
  namespace: dba-gpt
spec:
  selector:
    app: dba-gpt
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8501
  type: LoadBalancer
```

### Create Ingress
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dba-gpt-ingress
  namespace: dba-gpt
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - dba-gpt.yourdomain.com
    secretName: dba-gpt-tls
  rules:
  - host: dba-gpt.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: dba-gpt-service
            port:
              number: 80
```

## 🔒 Security Hardening

### 1. Network Security
```bash
# Configure firewall rules
sudo ufw allow 8501/tcp
sudo ufw allow 22/tcp
sudo ufw enable

# Use reverse proxy (nginx)
sudo apt install nginx
```

### 2. SSL/TLS Configuration
```nginx
# /etc/nginx/sites-available/dba-gpt
server {
    listen 443 ssl http2;
    server_name dba-gpt.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/dba-gpt.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dba-gpt.yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Environment Variables
```bash
# /etc/environment
DBA_ENV=production
MYSQL_HOST=your-mysql-host
MYSQL_DATABASE=your-database
MYSQL_USERNAME=your-username
MYSQL_PASSWORD=your-secure-password
JWT_SECRET=your-very-long-random-jwt-secret
OPENAI_API_KEY=your-openai-api-key
```

## 📊 Monitoring & Alerting

### 1. Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'dba-gpt'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
```

### 2. Grafana Dashboard
```json
{
  "dashboard": {
    "title": "DBA-GPT Production Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Database Connection Pool",
        "type": "stat",
        "targets": [
          {
            "expr": "db_connections_active",
            "legendFormat": "Active Connections"
          }
        ]
      }
    ]
  }
}
```

### 3. Alert Rules
```yaml
# alerts.yml
groups:
  - name: dba-gpt
    rules:
      - alert: HighErrorRate
        expr: rate(http_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
      
      - alert: DatabaseConnectionFailure
        expr: db_connections_failed > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failures"
          description: "{{ $value }} database connection failures detected"
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v2
      with:
        context: .
        file: ./Dockerfile.production
        push: true
        tags: ghcr.io/${{ github.repository }}:production
    
    - name: Deploy to Kubernetes
      uses: steebchen/kubectl@v2
      with:
        config: ${{ secrets.KUBE_CONFIG_DATA }}
        command: set image deployment/dba-gpt dba-gpt=ghcr.io/${{ github.repository }}:production -n dba-gpt
```

## 🧪 Testing Production Deployment

### 1. Smoke Tests
```bash
# Test basic functionality
curl -f http://your-domain:8501/_stcore/health
curl -f http://your-domain:8501/api/health

# Test database connectivity
curl -X POST http://your-domain:8501/api/test-connection \
  -H "Content-Type: application/json" \
  -d '{"database": "production_mysql"}'
```

### 2. Load Testing
```bash
# Install k6
curl -L https://github.com/grafana/k6/releases/download/v0.45.0/k6-v0.45.0-linux-amd64.tar.gz | tar xz

# Run load test
./k6 run load-test.js
```

### 3. Security Testing
```bash
# Run security scan
docker run --rm -v $(pwd):/app owasp/zap2docker-stable zap-baseline.py -t http://your-domain:8501
```

## 📈 Scaling Considerations

### 1. Horizontal Scaling
- Use Kubernetes HPA (Horizontal Pod Autoscaler)
- Implement database read replicas
- Use Redis for session storage

### 2. Vertical Scaling
- Monitor resource usage
- Adjust CPU/memory limits
- Optimize database queries

### 3. Database Scaling
- Implement connection pooling
- Use database clustering
- Consider sharding for large datasets

## 🚨 Emergency Procedures

### 1. Rollback Plan
```bash
# Quick rollback to previous version
kubectl rollout undo deployment/dba-gpt -n dba-gpt

# Or rollback to specific revision
kubectl rollout undo deployment/dba-gpt --to-revision=2 -n dba-gpt
```

### 2. Incident Response
- Document incident timeline
- Communicate with stakeholders
- Execute recovery procedures
- Post-incident review

## 📋 Production Checklist

- [ ] Security audit completed
- [ ] Performance testing passed
- [ ] Monitoring configured
- [ ] Backup procedures tested
- [ ] Disaster recovery plan ready
- [ ] Team training completed
- [ ] Documentation updated
- [ ] Support procedures defined
- [ ] SLA requirements met
- [ ] Compliance requirements satisfied

## 🎉 Go-Live Steps

1. **Final Testing**: Run full test suite
2. **Backup**: Create backup of current system
3. **Deploy**: Execute deployment pipeline
4. **Verify**: Run health checks and smoke tests
5. **Monitor**: Watch metrics and logs closely
6. **Announce**: Notify users of new system
7. **Support**: Provide immediate support coverage

## 📞 Support & Maintenance

- **24/7 Monitoring**: Set up alerting for critical issues
- **Regular Updates**: Schedule maintenance windows
- **Performance Reviews**: Monthly performance analysis
- **Security Updates**: Regular security patches
- **User Training**: Ongoing user education

---

**Remember**: Production deployment is a significant milestone, but it's also the beginning of ongoing operations. Maintain vigilance, monitor performance, and continuously improve your system based on real-world usage patterns.

