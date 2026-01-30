# 🚀 START PRODUCTION - Quick Reference

## Pre-Flight Checks

Run this before starting:
```bash
python scripts/validate_startup.py
```

Expected output:
```
✅ Python Version
✅ All required files
✅ BigQuery credentials
✅ BigQuery connection
✅ All dependencies installed
✅ Ports available
```

---

## Start Commands

### **1. Start API Server**
```bash
# Development
uvicorn api.main:app --reload --port 8000

# Production
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### **2. Start Streamlit Dashboard** (Legacy UI)
```bash
streamlit run titan_app.py
```

### **3. Run Tests**
```bash
# All tests
python scripts/test_everything.py

# Expected: 33/33 PASSED
```

---

## API Endpoints

### **Health Check**
```bash
curl http://localhost:8000/health
```

### **API Documentation**
Open in browser: http://localhost:8000/docs

### **Create Ledger Entry**
```bash
curl -X POST http://localhost:8000/ledger/entries \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "cafe_mellow",
    "location_id": "koramangala",
    "timestamp": "2026-01-25T10:00:00Z",
    "entry_date": "2026-01-25",
    "type": "SALE",
    "amount": 1500.50,
    "entry_source": "pos_petpooja",
    "category": "Food Sales",
    "description": "Pizza order"
  }'
```

### **Query Ledger Entries**
```bash
curl "http://localhost:8000/ledger/entries?org_id=cafe_mellow&location_id=koramangala&start_date=2026-01-01&end_date=2026-01-31&limit=100"
```

### **Check Data Quality**
```bash
curl "http://localhost:8000/analytics/data_quality?org_id=cafe_mellow&location_id=koramangala&days=30"
```

### **Calculate Profit (Adaptive)**
```bash
curl "http://localhost:8000/analytics/profit?org_id=cafe_mellow&location_id=koramangala&start_date=2026-01-01&end_date=2026-01-31"
```

---

## Environment Variables Required

### **Minimum Required**
```bash
# No environment variables required for basic operation
# Service key must exist: service-key.json
```

### **For Full Functionality**
```bash
export GEMINI_API_KEY="your_gemini_api_key"
export CRON_SECRET="your_random_secret_32_chars"

# Optional (for file uploads)
export R2_ACCOUNT_ID="your_cloudflare_account"
export R2_ACCESS_KEY_ID="your_r2_key"
export R2_SECRET_ACCESS_KEY="your_r2_secret"
export R2_BUCKET_NAME="titan-erp-files"
```

---

## Troubleshooting

### API won't start
```bash
# Check if port is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <process_id> /F
```

### BigQuery connection fails
```bash
# Verify service key exists
dir service-key.json

# Test BigQuery connection
python -c "from google.cloud import bigquery; client = bigquery.Client.from_service_account_json('service-key.json'); print('✅ Connected')"
```

### Tests failing
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Run tests with verbose output
python scripts/test_everything.py
```

---

## Quick Links

- **API Docs:** http://localhost:8000/docs
- **Streamlit:** http://localhost:8501
- **Health Check:** http://localhost:8000/health
- **Cron Health:** http://localhost:8000/cron/health

---

## Production Checklist

Before deploying to production:

- [ ] Run `python scripts/validate_startup.py` - all checks pass
- [ ] Run `python scripts/test_everything.py` - 33/33 pass
- [ ] Set CRON_SECRET environment variable
- [ ] Set GEMINI_API_KEY environment variable
- [ ] Configure R2 storage (if using file uploads)
- [ ] Setup Cloud Scheduler cron jobs
- [ ] Enable Cloud Logging
- [ ] Set up monitoring alerts
- [ ] Configure budget alerts for BigQuery

---

**Status:** ✅ PRODUCTION READY  
**Last Tested:** 2026-01-25  
**Test Results:** 33/33 PASSED
