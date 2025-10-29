# Deployment Guide: Project GEO

**Last Updated**: October 29, 2025  
**Version**: 2.0.0 (Production-Ready)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Monitoring Setup](#monitoring-setup)
6. [Troubleshooting](#troubleshooting)
7. [Production Checklist](#production-checklist)

---

## Prerequisites

### Required Software

- **Docker**: 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: 2.0+ (included with Docker Desktop)
- **Node.js**: 18.0+ ([Install Node.js](https://nodejs.org/))
- **Python**: 3.11+ ([Install Python](https://www.python.org/downloads/))
- **Git**: 2.0+

### Optional for Kubernetes

- **kubectl**: 1.25+ ([Install kubectl](https://kubernetes.io/docs/tasks/tools/))
- **Helm**: 3.0+ ([Install Helm](https://helm.sh/docs/intro/install/))
- **k9s**: Latest (recommended for cluster management)

---

## Local Development

### 1. Clone Repository

```bash
git clone https://github.com/your-org/GEO.git
cd GEO
```

### 2. Setup Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start Neo4j (Docker)
docker run -d \
  --name neo4j \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:5.13

# Run backend
python -m uvicorn src.backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend should be accessible at**: `http://localhost:8000`

### 3. Setup Frontend

```bash
# Navigate to frontend
cd apps/web

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local with backend URL

# Run frontend
npm run dev
```

**Frontend should be accessible at**: `http://localhost:3000`

### 4. Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend (in browser)
open http://localhost:3000

# View Prometheus metrics
curl http://localhost:8000/metrics
```

---

## Docker Deployment

### Development Mode

**Quick Start** (simplest):

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

**Services Started**:
- Neo4j: `http://localhost:7474` (Browser), `bolt://localhost:7687` (Bolt)
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

### Production Mode

**Step 1: Create Production Environment File**

```bash
# Copy example
cp .env.prod.example .env.prod

# Edit with production values
nano .env.prod
```

**Example `.env.prod`**:
```bash
# Database
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<strong-random-password>

# API
GEO_API_KEY=<strong-api-key>

# Logging
LOG_LEVEL=INFO
USE_JSON_LOGGING=true

# Monitoring
ENABLE_METRICS=true

# LLM (configure your provider)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

**Step 2: Build and Deploy**

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

**Step 3: Verify Deployment**

```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/health/ready

# Access services
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
echo "Neo4j Browser: http://localhost:7474"
echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3001"
```

**Grafana Default Credentials**:
- Username: `admin`
- Password: `admin` (change on first login)

### Scaling

```bash
# Scale backend to 3 instances
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# View scaled instances
docker-compose -f docker-compose.prod.yml ps backend
```

### Updating

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose -f docker-compose.prod.yml build

# Restart services (zero-downtime with rolling restart)
docker-compose -f docker-compose.prod.yml up -d --no-deps backend
docker-compose -f docker-compose.prod.yml up -d --no-deps frontend
```

### Backup & Restore

**Backup Neo4j Database**:
```bash
# Stop Neo4j
docker-compose -f docker-compose.prod.yml stop neo4j

# Create backup
docker run --rm \
  --volumes-from <neo4j-container-id> \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/neo4j-backup-$(date +%Y%m%d).tar.gz /data

# Restart Neo4j
docker-compose -f docker-compose.prod.yml start neo4j
```

**Restore Neo4j Database**:
```bash
# Stop Neo4j
docker-compose -f docker-compose.prod.yml stop neo4j

# Restore backup
docker run --rm \
  --volumes-from <neo4j-container-id> \
  -v $(pwd)/backups:/backup \
  ubuntu bash -c "cd / && tar xzf /backup/neo4j-backup-20251029.tar.gz"

# Restart Neo4j
docker-compose -f docker-compose.prod.yml start neo4j
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or local with minikube)
- `kubectl` configured to access your cluster
- Ingress controller (nginx-ingress recommended)

### Step 1: Create Namespace

```bash
kubectl create namespace geo-production
kubectl config set-context --current --namespace=geo-production
```

### Step 2: Create Secrets

```bash
# Neo4j password
kubectl create secret generic neo4j-secrets \
  --from-literal=password=<strong-password>

# API key
kubectl create secret generic api-secrets \
  --from-literal=geo-api-key=<strong-api-key>

# LLM API key (if using OpenAI/Anthropic)
kubectl create secret generic llm-secrets \
  --from-literal=openai-api-key=sk-...
```

### Step 3: Deploy Neo4j

```yaml
# k8s/neo4j.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: neo4j-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
spec:
  serviceName: neo4j
  replicas: 1
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
    spec:
      containers:
      - name: neo4j
        image: neo4j:5.13
        ports:
        - containerPort: 7474
          name: http
        - containerPort: 7687
          name: bolt
        env:
        - name: NEO4J_AUTH
          valueFrom:
            secretKeyRef:
              name: neo4j-secrets
              key: password
        - name: NEO4J_PLUGINS
          value: '["apoc"]'
        - name: NEO4J_dbms_memory_heap_initial__size
          value: "2G"
        - name: NEO4J_dbms_memory_heap_max__size
          value: "2G"
        volumeMounts:
        - name: data
          mountPath: /data
        livenessProbe:
          tcpSocket:
            port: 7687
          initialDelaySeconds: 60
        readinessProbe:
          tcpSocket:
            port: 7687
          initialDelaySeconds: 30
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 50Gi
---
apiVersion: v1
kind: Service
metadata:
  name: neo4j
spec:
  selector:
    app: neo4j
  ports:
  - name: http
    port: 7474
  - name: bolt
    port: 7687
```

**Apply**:
```bash
kubectl apply -f k8s/neo4j.yaml
```

### Step 4: Deploy Backend

```yaml
# k8s/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: ghcr.io/<your-org>/geo-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: NEO4J_URI
          value: "bolt://neo4j:7687"
        - name: NEO4J_USER
          value: "neo4j"
        - name: NEO4J_PASSWORD
          valueFrom:
            secretKeyRef:
              name: neo4j-secrets
              key: password
        - name: GEO_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: geo-api-key
        - name: LOG_LEVEL
          value: "INFO"
        - name: USE_JSON_LOGGING
          value: "true"
        - name: ENABLE_METRICS
          value: "true"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 10
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2"
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8000"
    prometheus.io/path: "/metrics"
spec:
  selector:
    app: backend
  ports:
  - port: 8000
```

**Apply**:
```bash
kubectl apply -f k8s/backend.yaml
```

### Step 5: Deploy Frontend

```yaml
# k8s/frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: ghcr.io/<your-org>/geo-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: NEXT_PUBLIC_API_BASE
          value: "http://backend:8000"
        livenessProbe:
          httpGet:
            path: /
            port: 3000
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /
            port: 3000
          initialDelaySeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  selector:
    app: frontend
  ports:
  - port: 3000
```

**Apply**:
```bash
kubectl apply -f k8s/frontend.yaml
```

### Step 6: Configure Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: geo-ingress
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - geo.yourdomain.com
    secretName: geo-tls
  rules:
  - host: geo.yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
```

**Apply**:
```bash
kubectl apply -f k8s/ingress.yaml
```

### Step 7: Deploy Monitoring

```bash
# Add Prometheus Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus + Grafana
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace geo-production \
  --set grafana.adminPassword=<strong-password>
```

### Verify Deployment

```bash
# Check all pods
kubectl get pods

# Check services
kubectl get services

# Check ingress
kubectl get ingress

# View logs
kubectl logs -f deployment/backend
kubectl logs -f deployment/frontend

# Port forward for testing
kubectl port-forward service/frontend 3000:3000
kubectl port-forward service/backend 8000:8000
```

---

## Monitoring Setup

### Prometheus Configuration

Prometheus is configured via `monitoring/prometheus.yml` and automatically deployed with docker-compose or Kubernetes.

**Key Metrics to Monitor**:

1. **Request Rate**: `rate(geo_requests_total[5m])`
2. **Error Rate**: `rate(geo_requests_total{status=~"5.."}[5m])`
3. **Latency (p95)**: `histogram_quantile(0.95, geo_request_duration_seconds)`
4. **Active Requests**: `geo_active_requests`
5. **Cache Hit Rate**: `geo_cache_hits_total / (geo_cache_hits_total + geo_cache_misses_total)`

### Grafana Dashboards

**Import Dashboard** (after deployment):

1. Open Grafana: `http://localhost:3001` (Docker) or via Kubernetes ingress
2. Login with admin credentials
3. Go to **Dashboards** → **Import**
4. Upload `monitoring/grafana-dashboard.json` (create from template below)

**Dashboard Panels** (to create manually or import):

- **Overview Panel**: Total requests, errors, active requests
- **Performance Panel**: Request duration (p50, p95, p99), throughput
- **RAG Panel**: Query rate, facts retrieved, cache hit rate
- **Database Panel**: Neo4j query duration, errors
- **System Panel**: CPU, memory, disk usage

---

## Troubleshooting

### Health Check Failures

**Problem**: `/health/ready` returns 503

**Diagnosis**:
```bash
# Check health endpoint
curl -v http://localhost:8000/health/ready

# Check Neo4j connection
docker logs <neo4j-container>

# Check backend logs
docker logs <backend-container>
```

**Solutions**:
- Ensure Neo4j is running: `docker ps | grep neo4j`
- Check Neo4j credentials in environment
- Verify network connectivity: `docker network ls`
- Check Neo4j logs for errors

### High Memory Usage

**Problem**: Backend container using >2GB memory

**Diagnosis**:
```bash
# Check container stats
docker stats <backend-container>

# Check Python memory
docker exec <backend-container> python -c "import psutil; print(psutil.virtual_memory())"
```

**Solutions**:
- Adjust heap size in `config.py`
- Clear caches: `POST /admin/cache/clear`
- Reduce batch sizes for ingestion
- Increase container memory limits

### Slow Queries

**Problem**: `/ask` endpoint taking >10s

**Diagnosis**:
```bash
# Check metrics
curl http://localhost:8000/metrics | grep geo_rag_query_duration

# Check Neo4j query performance
# Open Neo4j Browser: http://localhost:7474
# Run: CALL dbms.listQueries()
```

**Solutions**:
- Create indexes: `CREATE INDEX FOR (f:Fact) ON (f.embedding_id)`
- Optimize Neo4j heap size
- Check embedding model loading time
- Review query expansion settings

### Container Won't Start

**Problem**: Backend container crashes on startup

**Diagnosis**:
```bash
# View logs
docker logs <backend-container>

# Check if port is already in use
lsof -i :8000

# Check environment variables
docker inspect <backend-container> | grep Env
```

**Solutions**:
- Ensure all required env vars are set
- Check for port conflicts
- Verify Docker network exists
- Check file permissions (especially for volumes)

---

## Production Checklist

### Pre-Deployment

- [ ] **Secrets**: All sensitive data in secrets/environment variables (not hardcoded)
- [ ] **Passwords**: Strong passwords for Neo4j, Grafana, API keys
- [ ] **SSL/TLS**: HTTPS enabled for frontend and API
- [ ] **Firewall**: Ports properly configured (only 443/80 exposed publicly)
- [ ] **Backups**: Automated backup system for Neo4j database
- [ ] **Monitoring**: Prometheus and Grafana configured with alerts
- [ ] **Logging**: Structured JSON logging enabled
- [ ] **Health Checks**: All health endpoints tested
- [ ] **Resource Limits**: CPU/memory limits set appropriately
- [ ] **Scaling**: Horizontal pod autoscaling configured (if Kubernetes)

### Post-Deployment

- [ ] **Smoke Tests**: Basic functionality verified
- [ ] **Load Tests**: System tested under expected load
- [ ] **Monitoring**: Dashboards showing green health
- [ ] **Alerts**: Alert rules tested and notifications working
- [ ] **Backup**: First backup completed successfully
- [ ] **Documentation**: Runbooks created for common issues
- [ ] **Incident Response**: On-call rotation and escalation defined
- [ ] **Rollback Plan**: Tested rollback procedure

### Security Checklist

- [ ] **API Authentication**: API keys required for all requests
- [ ] **Rate Limiting**: Implemented per-IP or per-user
- [ ] **Input Validation**: All user inputs sanitized
- [ ] **HTTPS**: SSL certificates valid and auto-renewing
- [ ] **CORS**: Configured to allow only trusted origins
- [ ] **Secrets Rotation**: Process for rotating API keys/passwords
- [ ] **Audit Logging**: Security events logged and monitored
- [ ] **Dependency Scanning**: Regular vulnerability scans
- [ ] **Network Policies**: Kubernetes network policies configured

---

## Support

### Documentation

- **API Reference**: See `docs/API_REFERENCE.md`
- **Architecture**: See `docs/ARCHITECTURE.md`
- **Options D & E**: See `docs/OPTIONS_D_E_COMPLETE.md`

### Community

- **GitHub Issues**: [github.com/your-org/GEO/issues](https://github.com/your-org/GEO/issues)
- **Discussions**: [github.com/your-org/GEO/discussions](https://github.com/your-org/GEO/discussions)

### Commercial Support

- **Email**: support@yourdomain.com
- **Enterprise**: enterprise@yourdomain.com

---

*Last Updated*: October 29, 2025  
*Version*: 2.0.0  
*Maintainer*: Project GEO Team
