# 🛡️ Module: Master Dashboard (The Admin)

**Version:** 1.0.0  
**Status:** ✅ Production-Ready  
**Last Updated:** January 31, 2026

---

## Purpose

The **Master Module** is the administrative backbone of TITAN. It provides:
- **Tenant Registry** - Multi-tenant SaaS management
- **Health Monitor** - System uptime and performance tracking
- **Feature Flags** - Dynamic feature enablement per tenant
- **Usage Tracking** - API usage and billing metrics
- **AI Watchdog** - Monitors AI performance and costs

---

## 📂 Architecture

```
backend/master/
├── README.md              # This file (Module Passport)
├── tenant_registry.py     # ⭐ Multi-tenant management
├── health_monitor.py      # System health & uptime
├── feature_manager.py     # Feature flags per tenant
├── usage_tracker.py       # API usage & billing
└── ai_watchdog.py         # AI cost & performance monitoring
```

---

## 🔑 Key Components

### 1. `tenant_registry.py` (The Auth)
Manages multi-tenant registration and configuration.

**Key Class:** `TenantRegistry`

**Capabilities:**
- Register new tenants
- Store tenant-specific configuration
- Manage tenant quotas and limits
- Tenant isolation enforcement

**BigQuery Table:** `tenant_registry`

---

### 2. `health_monitor.py` (The Pulse)
Monitors system health and uptime.

**Key Class:** `HealthMonitor`

**Metrics Tracked:**
| Metric | Description |
|--------|-------------|
| API Response Time | Average latency per endpoint |
| Error Rate | 4xx/5xx errors per hour |
| BigQuery Health | Query success rate |
| AI Availability | Gemini API status |

**BigQuery Table:** `system_health_log`

---

### 3. `feature_manager.py` (The Switches)
Dynamic feature flags for gradual rollouts.

**Key Class:** `FeatureManager`

**Example Flags:**
```python
{
  "tenant_id": "cafe-mellow",
  "features": {
    "ai_chat_v3": True,
    "advanced_analytics": True,
    "pdf_ingestion": False,  # Coming soon
    "voice_input": True
  }
}
```

**BigQuery Table:** `feature_flags`

---

### 4. `usage_tracker.py` (The Meter)
Tracks API usage for billing and quotas.

**Key Class:** `UsageTracker`

**Metrics:**
- API calls per tenant per day
- BigQuery bytes scanned
- AI tokens consumed
- Storage usage

**BigQuery Table:** `usage_metrics`

---

### 5. `ai_watchdog.py` (The Guardian)
Monitors AI costs and performance.

**Key Class:** `AIWatchdog`

**Alerts:**
- High token consumption (>10K/hour)
- Slow response times (>5s)
- Error rate spikes
- Budget threshold warnings

**BigQuery Table:** `ai_performance_log`

---

## 🚀 API Endpoints

### System Health
```
GET /api/v1/titan/v3/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "uptime": "99.9%",
  "components": {
    "api": "ok",
    "bigquery": "ok",
    "gemini": "ok",
    "frontend": "ok"
  },
  "last_check": "2026-01-31T00:00:00Z"
}
```

---

### Master Dashboard Stats
```
GET /api/v1/master/stats
```

**Response:**
```json
{
  "total_tenants": 15,
  "active_today": 12,
  "api_calls_today": 4523,
  "ai_tokens_today": 125000,
  "error_rate": "0.2%"
}
```

---

### Tenant Management
```
GET /api/v1/master/tenants
POST /api/v1/master/tenants
GET /api/v1/master/tenants/{tenant_id}
PUT /api/v1/master/tenants/{tenant_id}
```

---

### Feature Flags
```
GET /api/v1/master/features/{tenant_id}
PUT /api/v1/master/features/{tenant_id}
```

---

## 🔧 Configuration

Uses centralized config from `pillars/config_vault.py`:
```python
from pillars.config_vault import get_bq_config

PROJECT_ID, DATASET_ID = get_bq_config()
```

**Environment Variables:**
- `PROJECT_ID` - BigQuery project ID
- `DATASET_ID` - BigQuery dataset name
- `KEY_FILE` - Service account key path

---

## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/api/v1/titan/v3/health

# Master stats (requires admin auth)
curl http://localhost:8000/api/v1/master/stats \
  -H "Authorization: Bearer <admin_token>"
```

---

## 📚 Related Modules

- **Master Router:** `api/routers/master.py` - API endpoint wrapper
- **Config Vault:** `pillars/config_vault.py` - Centralized configuration
- **TITAN v3:** `backend/core/titan_v3/` - AI engine integration

---

## 🔐 Access Control

Master endpoints require **admin role** authentication:
- Only users with `role: admin` can access `/api/v1/master/*`
- Regular users get 403 Forbidden

---

**Built with 🔥 by the TITAN Evolution Engine**
