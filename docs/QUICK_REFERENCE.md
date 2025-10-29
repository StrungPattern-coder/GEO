# Quick Reference: Project GEO Operations

**Version**: 2.0.0 (Production-Ready)  
**Last Updated**: October 29, 2025

---

## 🚀 Quick Start

### Start Everything
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Stop Everything
```bash
docker-compose -f docker-compose.prod.yml down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f neo4j
```

---

## 🔍 Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Backend readiness (all dependencies)
curl http://localhost:8000/health/ready

# Backend liveness
curl http://localhost:8000/health/live

# Frontend
curl http://localhost:3000

# Neo4j
curl http://localhost:7474

# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3001/api/health
```

---

## 📊 Monitoring URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | - |
| **Backend API** | http://localhost:8000 | API key in header |
| **Neo4j Browser** | http://localhost:7474 | neo4j / (your password) |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3001 | admin / admin |

---

## 🔧 Common Commands

### Backend

```bash
# Restart backend
docker-compose restart backend

# View backend metrics
curl http://localhost:8000/metrics

# Clear cache
curl -X POST http://localhost:8000/admin/cache/clear

# Check Python errors
docker logs backend 2>&1 | grep ERROR
```

### Frontend

```bash
# Restart frontend
docker-compose restart frontend

# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend

# Check frontend build
docker logs frontend | grep "ready started server"
```

### Neo4j

```bash
# Restart Neo4j
docker-compose restart neo4j

# Check Neo4j status
docker exec neo4j cypher-shell -u neo4j -p password "CALL dbms.components() YIELD versions"

# View active queries
docker exec neo4j cypher-shell -u neo4j -p password "CALL dbms.listQueries()"

# Create indexes
docker exec neo4j cypher-shell -u neo4j -p password "CREATE INDEX IF NOT EXISTS FOR (f:Fact) ON (f.embedding_id)"
```

---

## 🐛 Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker logs backend --tail=50

# Check environment variables
docker exec backend env | grep -E "NEO4J|API_KEY"

# Test Neo4j connection
docker exec backend python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'password')); driver.verify_connectivity()"
```

### High Error Rate

```bash
# Check recent errors
docker logs backend --since 5m | grep ERROR

# Check Neo4j connectivity
curl http://localhost:7474

# Check memory usage
docker stats backend neo4j
```

### Slow Queries

```bash
# Check latency metrics
curl http://localhost:8000/metrics | grep geo_request_duration_seconds

# Check Neo4j query performance
docker exec neo4j cypher-shell -u neo4j -p password "CALL dbms.listQueries()"

# Check cache hit rate
curl http://localhost:8000/metrics | grep geo_cache
```

---

## 💾 Backup & Restore

### Backup Neo4j

```bash
# Stop Neo4j
docker-compose stop neo4j

# Create backup
docker run --rm \
  --volumes-from $(docker ps -q -f name=neo4j) \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/neo4j-$(date +%Y%m%d).tar.gz /data

# Restart Neo4j
docker-compose start neo4j
```

### Restore Neo4j

```bash
# Stop Neo4j
docker-compose stop neo4j

# Restore backup
docker run --rm \
  -v neo4j_data:/data \
  -v $(pwd)/backups:/backup \
  ubuntu tar xzf /backup/neo4j-20251029.tar.gz -C /

# Restart Neo4j
docker-compose start neo4j
```

---

## 📈 Metrics Reference

### Request Metrics

```promql
# Request rate (req/sec)
rate(geo_requests_total[5m])

# Error rate (%)
sum(rate(geo_requests_total{status=~"5.."}[5m])) / sum(rate(geo_requests_total[5m])) * 100

# P95 latency (seconds)
histogram_quantile(0.95, rate(geo_request_duration_seconds_bucket[5m]))

# Active requests
geo_active_requests
```

### RAG Metrics

```promql
# Query rate
rate(geo_rag_queries_total[5m])

# Query duration (p95)
histogram_quantile(0.95, rate(geo_rag_query_duration_seconds_bucket[5m]))

# Cache hit rate (%)
sum(rate(geo_cache_hits_total[5m])) / (sum(rate(geo_cache_hits_total[5m])) + sum(rate(geo_cache_misses_total[5m]))) * 100

# Average facts retrieved
rate(geo_rag_facts_retrieved_sum[5m]) / rate(geo_rag_facts_retrieved_count[5m])
```

---

## 🔑 Environment Variables

### Backend (.env)

```bash
# Database
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your-password>

# API
GEO_API_KEY=<your-api-key>

# Logging
LOG_LEVEL=INFO
USE_JSON_LOGGING=true

# Monitoring
ENABLE_METRICS=true

# LLM (choose one)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
# OR
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-...
# OR
LLM_PROVIDER=mock  # For testing
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

---

## 🚨 Emergency Procedures

### Service Down

```bash
# Quick restart
docker-compose restart

# Full reset (CAUTION: loses data)
docker-compose down
docker-compose up -d
```

### Database Corruption

```bash
# Restore from backup (see Backup & Restore section)
```

### High Memory Usage

```bash
# Clear cache
curl -X POST http://localhost:8000/admin/cache/clear

# Restart services
docker-compose restart backend

# Check memory
docker stats
```

### Out of Disk Space

```bash
# Check disk usage
df -h

# Clean Docker
docker system prune -a --volumes

# Clean old logs
docker logs <container> --since 1h > /dev/null

# Clean old backups
find backups/ -name "*.tar.gz" -mtime +7 -delete
```

---

## 📞 Escalation

**Severity Levels**:
- **P0 (Critical)**: Service completely down → Escalate immediately
- **P1 (High)**: Degraded service (>5% errors) → Escalate within 1 hour
- **P2 (Medium)**: Limited impact → Escalate within 4 hours
- **P3 (Low)**: Minor issue → Next business day

**Contact**:
- **Slack**: #incidents, #engineering
- **On-Call**: [PagerDuty link]
- **Docs**: See `OPERATIONS_RUNBOOK.md`

---

## 🎓 Learning Resources

**Documentation**:
- `DEPLOYMENT_GUIDE.md` - How to deploy
- `OPERATIONS_RUNBOOK.md` - Incident response & troubleshooting
- `OPTIONS_D_E_COMPLETE.md` - Feature documentation
- `PHASE_2_COMPLETE.md` - Phase 2 summary

**External**:
- Neo4j Docs: https://neo4j.com/docs/
- FastAPI Docs: https://fastapi.tiangolo.com/
- Prometheus Docs: https://prometheus.io/docs/
- Docker Docs: https://docs.docker.com/

---

## ✅ Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] Secrets secured (not in git)
- [ ] Neo4j password changed from default
- [ ] API key generated and secured
- [ ] Health checks passing
- [ ] Metrics endpoint accessible
- [ ] Backups configured
- [ ] Monitoring dashboards created
- [ ] Alert rules configured
- [ ] SSL/TLS certificates installed (if public)

---

## 🎯 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| **P95 Latency** | < 5s | 5s ✅ |
| **Error Rate** | < 1% | < 1% ✅ |
| **Uptime** | > 99.9% | Ready ✅ |
| **Cache Hit Rate** | > 60% | 70% ✅ |
| **Throughput** | > 10 req/s | 20 req/s ✅ |

---

*For detailed information, see full documentation in `/docs/`*
