# Operations Runbook: Project GEO

**Version**: 2.0.0  
**Last Updated**: October 29, 2025  
**Purpose**: Incident response, maintenance procedures, and operational playbooks

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Monitoring & Alerts](#monitoring--alerts)
3. [Incident Response](#incident-response)
4. [Common Issues](#common-issues)
5. [Maintenance Procedures](#maintenance-procedures)
6. [Performance Tuning](#performance-tuning)
7. [Disaster Recovery](#disaster-recovery)
8. [On-Call Guide](#on-call-guide)

---

## System Overview

### Architecture

```
┌─────────────┐
│  Frontend   │ (Next.js on :3000)
│  (React)    │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  Backend    │ (FastAPI on :8000)
│  (Python)   │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│   Neo4j     │ (Graph DB on :7687)
│  Database   │
└─────────────┘

Monitoring:
- Prometheus (:9090) scrapes /metrics
- Grafana (:3001) visualizes metrics
```

### Key Components

| Component | Port | Health Check | Purpose |
|-----------|------|--------------|---------|
| **Frontend** | 3000 | `http://localhost:3000/` | User interface |
| **Backend** | 8000 | `http://localhost:8000/health/ready` | API & RAG pipeline |
| **Neo4j** | 7687 (bolt), 7474 (http) | `bolt://localhost:7687` | Knowledge graph |
| **Prometheus** | 9090 | `http://localhost:9090/-/healthy` | Metrics collection |
| **Grafana** | 3001 | `http://localhost:3001/api/health` | Dashboards |

### Critical Paths

1. **Query Path**: Frontend → Backend `/ask` → Neo4j → LLM → Response
2. **Ingestion Path**: Backend `/ingest/arxiv` → Neo4j → Storage
3. **Health Path**: Load Balancer → Backend `/health/ready` → Neo4j

---

## Monitoring & Alerts

### Key Metrics

#### 1. Request Metrics

**Prometheus Queries**:
```promql
# Request rate (requests per second)
rate(geo_requests_total[5m])

# Error rate (%)
sum(rate(geo_requests_total{status=~"5.."}[5m])) / sum(rate(geo_requests_total[5m])) * 100

# Request duration (p95)
histogram_quantile(0.95, rate(geo_request_duration_seconds_bucket[5m]))

# Active requests
geo_active_requests
```

**Alert Rules**:
```yaml
# alerts/backend.yml
groups:
- name: backend_alerts
  rules:
  - alert: HighErrorRate
    expr: sum(rate(geo_requests_total{status=~"5.."}[5m])) / sum(rate(geo_requests_total[5m])) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Backend error rate above 5%"
      description: "Error rate is {{ $value }}%"

  - alert: HighLatency
    expr: histogram_quantile(0.95, rate(geo_request_duration_seconds_bucket[5m])) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Backend latency above 10s (p95)"
      description: "P95 latency is {{ $value }}s"
```

#### 2. RAG Pipeline Metrics

**Prometheus Queries**:
```promql
# Query rate
rate(geo_rag_queries_total[5m])

# Query duration (p95)
histogram_quantile(0.95, rate(geo_rag_query_duration_seconds_bucket[5m]))

# Facts retrieved (average)
rate(geo_rag_facts_retrieved_sum[5m]) / rate(geo_rag_facts_retrieved_count[5m])

# Cache hit rate (%)
sum(rate(geo_cache_hits_total[5m])) / (sum(rate(geo_cache_hits_total[5m])) + sum(rate(geo_cache_misses_total[5m]))) * 100
```

**Alert Rules**:
```yaml
- alert: LowCacheHitRate
  expr: sum(rate(geo_cache_hits_total[5m])) / (sum(rate(geo_cache_hits_total[5m])) + sum(rate(geo_cache_misses_total[5m]))) < 0.5
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Cache hit rate below 50%"
    description: "Cache hit rate is {{ $value }}%"
```

#### 3. Database Metrics

**Prometheus Queries**:
```promql
# Neo4j query duration (p95)
histogram_quantile(0.95, rate(geo_neo4j_query_duration_seconds_bucket[5m]))

# Neo4j errors
rate(geo_neo4j_errors_total[5m])
```

**Alert Rules**:
```yaml
- alert: Neo4jHighLatency
  expr: histogram_quantile(0.95, rate(geo_neo4j_query_duration_seconds_bucket[5m])) > 5
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Neo4j query latency above 5s"

- alert: Neo4jErrors
  expr: rate(geo_neo4j_errors_total[5m]) > 0.1
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Neo4j experiencing errors"
```

### Grafana Dashboards

**Import Instructions**: See `DEPLOYMENT_GUIDE.md` → Monitoring Setup

**Key Panels**:
1. **System Health**: Request rate, error rate, active requests
2. **Performance**: P50/P95/P99 latency, throughput
3. **RAG Pipeline**: Query rate, cache hit rate, facts retrieved
4. **Database**: Neo4j query duration, connection pool
5. **System Resources**: CPU, memory, disk

---

## Incident Response

### Severity Levels

| Severity | Impact | Response Time | Examples |
|----------|--------|---------------|----------|
| **P0 - Critical** | Service down | 15 minutes | All requests failing, database down |
| **P1 - High** | Degraded service | 1 hour | High error rate (>5%), slow responses |
| **P2 - Medium** | Limited impact | 4 hours | Single component issue, cache miss |
| **P3 - Low** | Minor issue | 24 hours | Logging errors, metrics missing |

### Incident Response Process

1. **Acknowledge**: Acknowledge alert in PagerDuty/Slack
2. **Assess**: Check Grafana dashboards, logs, health endpoints
3. **Communicate**: Post in #incidents channel with status
4. **Investigate**: Follow runbook for specific issue (see below)
5. **Mitigate**: Apply fix or workaround
6. **Verify**: Confirm metrics/logs show resolution
7. **Document**: Update incident log with RCA

### Communication Template

```markdown
**INCIDENT**: [Brief description]
**STATUS**: Investigating / Identified / Mitigating / Resolved
**SEVERITY**: P0 / P1 / P2 / P3
**IMPACT**: [User-facing impact]
**NEXT UPDATE**: [Time]

**Timeline**:
- HH:MM - Incident detected
- HH:MM - Root cause identified
- HH:MM - Fix deployed
- HH:MM - Resolved

**Root Cause**: [Brief explanation]
**Resolution**: [What was done]
```

---

## Common Issues

### 1. High Error Rate (5xx)

**Symptoms**:
- Alert: "HighErrorRate" fires
- Grafana shows spike in 5xx responses
- Users report errors on frontend

**Diagnosis**:
```bash
# Check backend logs for errors
docker logs backend --tail=100 | grep ERROR

# Or in Kubernetes
kubectl logs deployment/backend --tail=100 | grep ERROR

# Check specific error distribution
curl http://localhost:8000/metrics | grep geo_requests_total | grep "5.."

# Check health endpoint
curl http://localhost:8000/health/ready
```

**Common Causes**:

**A. Neo4j Connection Lost**

```bash
# Check Neo4j status
docker ps | grep neo4j
# Or
kubectl get pods -l app=neo4j

# Check Neo4j logs
docker logs neo4j --tail=50
# Or
kubectl logs -l app=neo4j --tail=50

# Test connection
curl http://localhost:7474/db/system/tx/commit -u neo4j:password
```

**Resolution**:
```bash
# Restart Neo4j
docker restart neo4j
# Or
kubectl rollout restart statefulset/neo4j

# Wait for health check to pass
watch -n 2 'curl -s http://localhost:8000/health/ready | jq'
```

**B. LLM API Timeout**

```bash
# Check backend logs for timeout errors
docker logs backend --tail=100 | grep -i timeout

# Check LLM provider status (e.g., OpenAI)
curl https://status.openai.com/api/v2/status.json
```

**Resolution**:
```bash
# Increase timeout in config
# Edit src/backend/config.py
llm_timeout_seconds = 30  # Increase from 10

# Restart backend
docker-compose restart backend
# Or
kubectl rollout restart deployment/backend
```

**C. Memory Exhaustion**

```bash
# Check container memory
docker stats backend
# Or
kubectl top pod -l app=backend

# Check Python memory usage
docker exec backend python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"
```

**Resolution**:
```bash
# Clear cache
curl -X POST http://localhost:8000/admin/cache/clear

# Increase memory limit in docker-compose.prod.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G  # Increase from 2G

# Restart
docker-compose -f docker-compose.prod.yml up -d
```

---

### 2. Slow Queries (High Latency)

**Symptoms**:
- Alert: "HighLatency" fires
- Users report slow response times
- P95 latency > 10s

**Diagnosis**:
```bash
# Check latency metrics
curl http://localhost:8000/metrics | grep geo_request_duration_seconds

# Check Neo4j query performance
# In Neo4j Browser (http://localhost:7474)
CALL dbms.listQueries()

# Check slow queries in logs
docker logs backend --tail=200 | grep "duration"
```

**Common Causes**:

**A. Missing Database Indexes**

```bash
# Check existing indexes (Neo4j Browser)
SHOW INDEXES
```

**Resolution**:
```cypher
# Create missing indexes
CREATE INDEX IF NOT EXISTS FOR (f:Fact) ON (f.embedding_id);
CREATE INDEX IF NOT EXISTS FOR (f:Fact) ON (f.subject);
CREATE INDEX IF NOT EXISTS FOR (f:Fact) ON (f.predicate);
CREATE INDEX IF NOT EXISTS FOR (s:Source) ON (s.url);
CREATE INDEX IF NOT EXISTS FOR (s:Source) ON (s.domain);
```

**B. Large Result Sets**

**Resolution**:
```python
# Reduce max_facts in src/backend/config.py
max_facts_per_query = 10  # Reduce from 20

# Restart backend
docker-compose restart backend
```

**C. Cold Start (Embeddings Model)**

**Resolution**:
```bash
# Pre-warm embeddings on startup
# Add to src/backend/api/main.py lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Pre-warming embeddings model...")
    embeddings_model.encode(["warmup query"])
    
    yield
    
    # Shutdown
    ...
```

---

### 3. Database Connection Failures

**Symptoms**:
- `/health/ready` returns 503
- Backend logs show "Failed to connect to Neo4j"
- All queries failing

**Diagnosis**:
```bash
# Check Neo4j status
docker ps -a | grep neo4j
kubectl get pods -l app=neo4j

# Check Neo4j logs
docker logs neo4j --tail=50
kubectl logs -l app=neo4j --tail=50

# Check network connectivity
docker exec backend ping neo4j
kubectl exec deployment/backend -- nc -zv neo4j 7687

# Check Neo4j credentials
docker exec backend env | grep NEO4J
```

**Resolution**:

**A. Neo4j Container Down**
```bash
# Restart Neo4j
docker start neo4j
# Or
kubectl rollout restart statefulset/neo4j

# Wait for startup (takes 30-60s)
watch -n 2 'docker logs neo4j --tail=5'
```

**B. Network Issue**
```bash
# Check Docker network
docker network ls
docker network inspect geo-network

# Recreate network if needed
docker-compose down
docker-compose up -d
```

**C. Wrong Credentials**
```bash
# Verify credentials in .env
cat .env | grep NEO4J

# Update and restart
docker-compose down
# Edit .env with correct password
docker-compose up -d
```

---

### 4. High Memory Usage

**Symptoms**:
- Alert: "HighMemoryUsage" fires
- Container OOM killed
- Backend slow or unresponsive

**Diagnosis**:
```bash
# Check memory usage
docker stats backend neo4j

# Check Python heap
docker exec backend python -c "
import psutil
mem = psutil.virtual_memory()
print(f'Used: {mem.used / 1e9:.2f}GB')
print(f'Available: {mem.available / 1e9:.2f}GB')
print(f'Percent: {mem.percent}%')
"

# Check Neo4j heap
docker exec neo4j bash -c 'echo "CALL dbms.queryJmx(\"java.lang:type=Memory\") YIELD attributes RETURN attributes" | cypher-shell -u neo4j -p password'
```

**Resolution**:

**A. Clear Backend Cache**
```bash
curl -X POST http://localhost:8000/admin/cache/clear
```

**B. Increase Container Limits**
```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G  # Increase
```

**C. Optimize Neo4j Heap**
```yaml
# docker-compose.prod.yml
services:
  neo4j:
    environment:
      - NEO4J_dbms_memory_heap_initial__size=4G
      - NEO4J_dbms_memory_heap_max__size=4G
```

**D. Reduce Batch Sizes**
```python
# src/backend/config.py
pdf_batch_size = 5  # Reduce from 10
ingest_batch_size = 50  # Reduce from 100
```

---

### 5. Frontend Not Loading

**Symptoms**:
- Users see blank page or loading spinner
- Browser console shows errors
- Frontend health check fails

**Diagnosis**:
```bash
# Check frontend container
docker ps | grep frontend
kubectl get pods -l app=frontend

# Check frontend logs
docker logs frontend --tail=50
kubectl logs -l app=frontend --tail=50

# Check backend connectivity
docker exec frontend curl http://backend:8000/health
```

**Resolution**:

**A. Backend Unreachable**
```bash
# Check NEXT_PUBLIC_API_BASE
docker exec frontend env | grep API_BASE

# Fix in .env and restart
NEXT_PUBLIC_API_BASE=http://backend:8000
docker-compose restart frontend
```

**B. Build Failed**
```bash
# Check build logs
docker logs frontend | grep ERROR

# Rebuild
docker-compose build frontend
docker-compose up -d frontend
```

**C. Port Conflict**
```bash
# Check if port 3000 in use
lsof -i :3000

# Kill process or change port
docker-compose down
# Edit docker-compose.yml to use different port
docker-compose up -d
```

---

## Maintenance Procedures

### Daily Tasks

**Morning Check** (10 minutes):
```bash
# 1. Check service health
curl http://localhost:8000/health/ready
curl http://localhost:3000

# 2. Review overnight errors
docker logs backend --since 24h | grep ERROR | wc -l

# 3. Check disk space
df -h | grep -E "neo4j|pdf"

# 4. Review metrics (open Grafana)
open http://localhost:3001
```

### Weekly Tasks

**System Maintenance** (30 minutes):

1. **Database Backup**
```bash
# Run backup script
./scripts/backup-neo4j.sh

# Verify backup
ls -lh backups/ | tail -5
```

2. **Log Rotation**
```bash
# Clear old logs (keep last 7 days)
find /var/log/geo -name "*.log" -mtime +7 -delete

# Or with Docker
docker exec backend find /app/logs -name "*.log" -mtime +7 -delete
```

3. **Cache Cleanup**
```bash
# Clear stale cache entries
curl -X POST http://localhost:8000/admin/cache/clear

# Clean old PDF cache
docker exec backend find /app/pdf_cache -name "*.pdf" -mtime +30 -delete
```

4. **Security Updates**
```bash
# Update dependencies
pip list --outdated
npm outdated

# Rebuild with updates
docker-compose build --no-cache
docker-compose up -d
```

### Monthly Tasks

**Comprehensive Review** (2 hours):

1. **Performance Analysis**
   - Review P95/P99 latency trends
   - Identify slow queries in Neo4j
   - Optimize expensive operations

2. **Capacity Planning**
   - Review disk usage trends
   - Check memory/CPU utilization
   - Plan scaling if needed

3. **Security Audit**
   - Review access logs for anomalies
   - Rotate API keys
   - Update SSL certificates

4. **Disaster Recovery Test**
   - Test backup restore procedure
   - Verify failover processes
   - Update runbooks

---

## Performance Tuning

### Backend Optimization

**1. Query Caching**

Enable aggressive caching for read-heavy workloads:

```python
# src/backend/config.py
cache_ttl_seconds = 3600  # 1 hour (increase from 300)
cache_size_mb = 1024  # 1GB (increase from 512)
```

**2. Connection Pooling**

Optimize Neo4j connection pool:

```python
# src/backend/graph/client.py
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    uri,
    auth=(username, password),
    max_connection_pool_size=50,  # Increase from 20
    connection_acquisition_timeout=60,  # Increase from 30
    max_transaction_retry_time=15
)
```

**3. Batch Processing**

Increase batch sizes for ingestion:

```python
# src/backend/config.py
ingest_batch_size = 200  # Increase from 100
pdf_batch_size = 20  # Increase from 10
```

### Database Optimization

**1. Indexes**

Ensure all frequently queried properties are indexed:

```cypher
-- Check index usage
CALL db.stats.retrieve('QUERIES') YIELD data
RETURN data;

-- Create composite indexes if needed
CREATE INDEX FOR (f:Fact) ON (f.subject, f.predicate);
```

**2. Memory Configuration**

Tune Neo4j memory for your workload:

```yaml
# docker-compose.prod.yml
environment:
  - NEO4J_dbms_memory_heap_initial__size=8G
  - NEO4J_dbms_memory_heap_max__size=8G
  - NEO4J_dbms_memory_pagecache_size=4G
```

**3. Query Optimization**

Profile slow queries:

```cypher
PROFILE MATCH (f:Fact {subject: "example"}) RETURN f;
```

### Frontend Optimization

**1. Bundle Size Reduction**

Analyze and reduce bundle:

```bash
npm run build
npm run analyze  # If configured

# Remove unused dependencies
npm prune
```

**2. Image Optimization**

Use Next.js Image component:

```tsx
import Image from 'next/image';

<Image src="/logo.png" width={200} height={100} alt="Logo" />
```

---

## Disaster Recovery

### Backup Strategy

**Neo4j Database**:
- **Frequency**: Daily at 2 AM UTC
- **Retention**: 7 daily, 4 weekly, 12 monthly
- **Storage**: S3 or equivalent object storage

**Backup Script** (`scripts/backup-neo4j.sh`):
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups
CONTAINER=neo4j

# Stop Neo4j writes
docker exec $CONTAINER cypher-shell -u neo4j -p password \
  "CALL dbms.cluster.setReadOnly(true)"

# Create backup
docker run --rm \
  --volumes-from $CONTAINER \
  -v $BACKUP_DIR:/backup \
  ubuntu tar czf /backup/neo4j-$DATE.tar.gz /data

# Resume writes
docker exec $CONTAINER cypher-shell -u neo4j -p password \
  "CALL dbms.cluster.setReadOnly(false)"

# Upload to S3
aws s3 cp $BACKUP_DIR/neo4j-$DATE.tar.gz s3://geo-backups/

# Clean old local backups (keep last 7 days)
find $BACKUP_DIR -name "neo4j-*.tar.gz" -mtime +7 -delete
```

### Restore Procedure

**Full System Restore** (estimated time: 30 minutes):

1. **Stop Services**
```bash
docker-compose down
# Or
kubectl scale deployment --all --replicas=0
```

2. **Restore Neo4j Data**
```bash
# Download backup
aws s3 cp s3://geo-backups/neo4j-20251029_020000.tar.gz /tmp/

# Extract to volume
docker run --rm \
  -v neo4j_data:/data \
  -v /tmp:/backup \
  ubuntu tar xzf /backup/neo4j-20251029_020000.tar.gz -C /
```

3. **Start Services**
```bash
docker-compose up -d
# Or
kubectl scale deployment --all --replicas=<original-count>
```

4. **Verify**
```bash
# Check health
curl http://localhost:8000/health/ready

# Verify data
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'
```

### RTO & RPO

- **RTO** (Recovery Time Objective): 30 minutes
- **RPO** (Recovery Point Objective): 24 hours (daily backups)

---

## On-Call Guide

### Escalation Path

1. **Primary On-Call**: First responder (15 min SLA)
2. **Secondary On-Call**: Escalate if no resolution in 1 hour
3. **Engineering Lead**: Escalate for P0 incidents
4. **CTO**: Escalate for prolonged P0 outages (>4 hours)

### Quick Reference

**Health Checks**:
```bash
# Full system check
curl http://localhost:8000/health/ready

# Individual components
curl http://localhost:8000/health        # Backend
curl http://localhost:3000               # Frontend
curl http://localhost:7474               # Neo4j
curl http://localhost:9090/-/healthy     # Prometheus
```

**Restart Services** (quick fix):
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend

# Kubernetes
kubectl rollout restart deployment/backend
```

**View Logs** (last 5 minutes):
```bash
docker logs backend --since 5m
docker logs frontend --since 5m
docker logs neo4j --since 5m
```

**Emergency Contacts**:
- **Slack**: #incidents, #engineering
- **PagerDuty**: [your-pagerduty-link]
- **Status Page**: [your-status-page]

### Post-Incident

**RCA Template** (`incidents/YYYY-MM-DD-incident-name.md`):

```markdown
# Incident: [Name]

**Date**: YYYY-MM-DD
**Duration**: HH:MM
**Severity**: P0/P1/P2/P3
**Impact**: [Description]

## Timeline

- HH:MM - Incident detected
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Fix deployed
- HH:MM - Incident resolved

## Root Cause

[Technical explanation]

## Resolution

[What was done to fix]

## Prevention

- [ ] Action item 1
- [ ] Action item 2
- [ ] Update monitoring
- [ ] Update runbook

## Lessons Learned

[What we learned]
```

---

*Last Updated*: October 29, 2025  
*Version*: 2.0.0  
*Maintainer*: DevOps Team
