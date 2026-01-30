# 🚀 TITAN ERP - Production Deployment Guide

**Ever Built Edition | Version 3.0.0-PRODUCTION**

---

## ✅ Pre-Deployment Checklist

### 1. Environment Configuration
- [ ] Create `.env` file with all credentials
- [ ] Upload new `service-key.json` (rotate old key)
- [ ] Set `GEMINI_API_KEY` for AI engine
- [ ] Configure Petpooja API credentials
- [ ] Set Google Drive folder IDs

### 2. Dependencies Installation

**Backend (Python):**
```bash
pip install -r requirements_production.txt
```

**Frontend (Node.js):**
```bash
cd web
npm install
```

### 3. Database Setup
```bash
# Verify BigQuery connection
python scripts/test_bq_connection.py

# Create required tables (auto-created on first run)
python scripts/ensure_tables.py
```

---

## 🎯 New Features Implemented

### Backend Infrastructure

#### 1. **Chat Router** (`api/routers/chat.py`)
- ✅ Streaming SSE chat with real-time responses
- ✅ Relational Intelligence: Auto Text-to-SQL
- ✅ Meta-Cognitive Learning API
- ✅ Conversation memory (last 10 messages)
- ✅ Vision API integration ready

**Endpoints:**
- `POST /api/v1/chat/stream` - Streaming chat
- `POST /api/v1/chat` - Non-streaming chat
- `POST /api/v1/chat/metacognitive/learn` - Save learned patterns
- `GET /api/v1/chat/metacognitive/strategies` - Get AI strategies
- `DELETE /api/v1/chat/metacognitive/strategies/{id}` - Delete strategy

#### 2. **Sync Router** (`api/routers/sync.py`)
- ✅ Manual sync endpoints for all data sources
- ✅ Background task execution with status tracking
- ✅ Master sync for all sources
- ✅ Real-time sync status polling

**Endpoints:**
- `POST /api/v1/sync/sales` - Sync Petpooja sales
- `POST /api/v1/sync/expenses` - Sync Drive expenses
- `POST /api/v1/sync/recipes` - Sync recipes
- `POST /api/v1/sync/purchases` - Sync purchases
- `POST /api/v1/sync/wastage` - Sync wastage logs
- `POST /api/v1/sync/all` - Master sync
- `GET /api/v1/sync/status/{type}` - Check sync status

#### 3. **Oracle Router** (`api/routers/oracle.py`)
- ✅ Vision API for image analysis (invoices, food quality, inventory)
- ✅ Digital Twin Simulator for What-If scenarios
- ✅ Deductive Reasoning Engine for root cause analysis
- ✅ Fraud Detection (KOT reconciliation placeholder)

**Endpoints:**
- `POST /api/v1/oracle/vision/analyze` - Image analysis
- `POST /api/v1/oracle/simulate` - Scenario simulation
- `POST /api/v1/oracle/deduce` - Deductive reasoning
- `GET /api/v1/oracle/fraud/kot-reconciliation` - Fraud detection

#### 4. **Forecast Router** (`api/routers/forecast.py`)
- ✅ Daily forecast with weather & holiday integration
- ✅ Predictive inventory requirements
- ✅ Staff recommendations
- ✅ 7-day rolling forecast

**Endpoints:**
- `POST /api/v1/forecast/daily` - Tomorrow's forecast
- `GET /api/v1/forecast/week` - 7-day predictions

#### 5. **Auto-Pilot Cron System** (`api/main.py`)
- ✅ Daily sync at 2 AM (automated)
- ✅ Daily brief generation at 6 AM
- ✅ APScheduler integration
- ✅ Background task execution

---

### Frontend Enhancements

#### 1. **Enhanced Settings** (`web/src/app/settings/SettingsEnhanced.tsx`)
**Three Tabs:**

**Credentials Tab:**
- Secure API key management
- BigQuery configuration
- Petpooja credentials
- Status indicators for all secrets

**Metacognitive Tab:**
- View AI learned strategies
- Approve/Reject/Delete patterns
- Confidence scores
- Usage tracking

**System Tab:**
- AI tone configuration (Professional/Friendly/Technical)
- Tax rate settings
- Historical backfill start date picker
- Auto-sync toggle (Daily 2 AM)
- **DANGER ZONE:** Database cache clear (Nuke button with confirmation)

#### 2. **Sync Control Component** (`web/src/components/SyncControl.tsx`)
- ✅ Manual sync buttons for each data source
- ✅ Real-time status tracking with polling
- ✅ Progress indicators
- ✅ Master sync button
- ✅ Success/failure toasts
- ✅ Visual sync progress bars

#### 3. **Error Boundary** (`web/src/components/ErrorBoundary.tsx`)
- ✅ React error handling wrapper
- ✅ Prevents white-screen crashes
- ✅ User-friendly error messages
- ✅ "Try Again" and "Reload Page" buttons
- ✅ Auto-logging to backend monitoring
- ✅ Stack trace in development mode

#### 4. **RBAC System** (`web/src/contexts/RBACContext.tsx`)
**Role Hierarchy:**
- **CEO:** Full access (all features)
- **Manager:** Operations + Reports (no credential editing)
- **Staff:** Dashboard + Chat + Operations
- **Viewer:** Dashboard only

**Permissions:**
- `view_dashboard`, `view_chat`, `view_operations`, `view_settings`
- `edit_credentials`, `trigger_sync`, `delete_data`
- `view_financials`, `export_reports`, `manage_users`

#### 5. **Voice Input** (`web/src/components/VoiceInput.tsx`)
- ✅ Web Speech API integration
- ✅ Real-time transcription
- ✅ Visual recording indicator
- ✅ Interim results preview
- ✅ Language support (default: en-IN)
- ✅ Graceful degradation (hidden if unsupported)

#### 6. **PDF Export** (`web/src/components/PDFExport.tsx`)
- ✅ One-click P&L PDF generation
- ✅ Professional formatting
- ✅ Revenue, expenses, profit breakdown
- ✅ Tax calculations (18% GST)
- ✅ Date range and generation timestamp
- ✅ Client-side PDF generation (jsPDF)

---

## 🔧 Integration Points

### Chat Integration
```typescript
// Update ChatClient.tsx to use new chat endpoint
const res = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ 
    message: text,
    org_id: tenant.org_id,
    location_id: tenant.location_id,
    enable_sql: true,
    enable_vision: false
  }),
});
```

### Voice + Chat Integration
```tsx
import VoiceInput from "@/components/VoiceInput";

<VoiceInput 
  onTranscript={(text) => {
    setInput(prev => prev + " " + text);
  }}
  language="en-IN"
/>
```

### Sync UI Integration (Dashboard)
```tsx
import SyncControl from "@/components/SyncControl";

// Add to dashboard page
<SyncControl />
```

### Error Boundary Wrapping
```tsx
import ErrorBoundary from "@/components/ErrorBoundary";

// Wrap major components
<ErrorBoundary>
  <DashboardClient />
</ErrorBoundary>
```

### RBAC Protection
```tsx
import { useRBAC } from "@/contexts/RBACContext";

const { hasPermission } = useRBAC();

{hasPermission("edit_credentials") && (
  <button>Edit Credentials</button>
)}
```

### PDF Export Integration
```tsx
import PDFExport from "@/components/PDFExport";

<PDFExport startDate={start} endDate={end} variant="button" />
```

---

## 🚦 Deployment Steps

### 1. Backend Deployment
```bash
# Navigate to project root
cd Cafe_AI

# Install dependencies
pip install -r requirements_production.txt

# Set environment variables
export PROJECT_ID="your-project-id"
export DATASET_ID="cafe_operations"
export GEMINI_API_KEY="your-gemini-key"

# Start API server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Production Server (Gunicorn):**
```bash
gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

### 2. Frontend Deployment
```bash
cd web

# Install dependencies
npm install

# Build for production
npm run build

# Start production server
npm start
```

**Or deploy to Vercel:**
```bash
vercel --prod
```

### 3. Cron Verification
```bash
# Check scheduler logs
tail -f logs/cron_scheduler.log

# Verify cron jobs are registered
curl http://localhost:8000/health
```

### 4. Database Verification
```bash
# Check all tables exist
python scripts/verify_tables.py

# Run test sync
curl -X POST http://localhost:8000/api/v1/sync/sales
```

---

## 🔐 Security Checklist

- [ ] Rotate all API keys before production
- [ ] Use Secret Manager (Google Cloud) for production secrets
- [ ] Enable HTTPS only (no HTTP)
- [ ] Set up CORS whitelist (remove `*` wildcards)
- [ ] Enable rate limiting on API endpoints
- [ ] Set up monitoring and alerts
- [ ] Configure backup strategy for BigQuery
- [ ] Enable audit logging
- [ ] Set up WAF (Web Application Firewall)
- [ ] Configure DDoS protection

---

## 📊 Monitoring & Observability

### API Health Check
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "ok": true,
  "bq_connected": true,
  "project_id": "your-project-id",
  "dataset_id": "cafe_operations",
  "gemini_key_set": true
}
```

### Sync Status Monitoring
```bash
curl http://localhost:8000/api/v1/sync/status
```

### Error Logs
```bash
# View application logs
tail -f logs/titan_system_log.txt

# Query BigQuery error logs
SELECT * FROM system_error_log 
ORDER BY created_at DESC 
LIMIT 100
```

---

## 🧪 Testing Protocol

### 1. Chat System Test
```bash
# Test non-streaming chat
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What were my expenses yesterday?",
    "org_id": "test_org",
    "location_id": "test_location"
  }'

# Test streaming chat (use browser or SSE client)
```

### 2. Sync System Test
```bash
# Test sales sync
curl -X POST http://localhost:8000/api/v1/sync/sales

# Check status
curl http://localhost:8000/api/v1/sync/status/sales
```

### 3. Forecast Test
```bash
curl -X POST http://localhost:8000/api/v1/forecast/daily \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "test_org",
    "location_id": "test_location",
    "forecast_date": "2026-01-27",
    "include_weather": true
  }'
```

### 4. Frontend Tests
- [ ] Chat with streaming works
- [ ] Voice input records and transcribes
- [ ] Manual sync buttons trigger and show status
- [ ] Settings tabs all functional
- [ ] Metacognitive strategies load and delete
- [ ] PDF export generates valid PDF
- [ ] Error boundary catches and displays errors
- [ ] RBAC hides features based on role

---

## 🎯 Performance Optimization

### Backend
- Use Redis for caching (future)
- Enable query result caching in BigQuery
- Implement connection pooling
- Use async where possible
- Enable gzip compression

### Frontend
- Enable Next.js static optimization
- Use dynamic imports for heavy components
- Implement lazy loading for images
- Enable CDN for static assets
- Minify and compress bundles

---

## 🆘 Troubleshooting

### Issue: Cron jobs not running
**Solution:** Check APScheduler installation and logs
```bash
pip install APScheduler==3.10.4
# Restart API server
```

### Issue: Voice input not working
**Solution:** Check browser support (Chrome/Edge required)
```javascript
// Check in browser console
console.log('webkitSpeechRecognition' in window);
```

### Issue: PDF export fails
**Solution:** Install jsPDF
```bash
cd web
npm install jspdf@^2.5.1
```

### Issue: Sync status always "unknown"
**Solution:** Wait 5-10 seconds after triggering sync for status to populate

### Issue: BigQuery connection fails
**Solution:** 
1. Verify service-key.json exists
2. Check service account has BigQuery Data Editor role
3. Verify PROJECT_ID and DATASET_ID are correct

---

## 📈 Post-Deployment Actions

1. **Monitor First 24 Hours:**
   - Check cron logs for automated syncs
   - Verify brief generation
   - Monitor error rates

2. **User Training:**
   - Demo AI chat features
   - Show manual sync process
   - Explain metacognitive learning

3. **Performance Tuning:**
   - Optimize slow queries
   - Adjust worker count based on load
   - Enable caching where beneficial

4. **Backup Strategy:**
   - Set up BigQuery snapshots
   - Export critical tables weekly
   - Test restore procedures

---

## 🎉 Success Criteria

- ✅ All API endpoints return 200 OK
- ✅ Cron jobs execute on schedule
- ✅ Chat responds in < 5 seconds
- ✅ Syncs complete without errors
- ✅ PDF exports generate valid files
- ✅ Voice input transcribes accurately
- ✅ Error boundary catches exceptions
- ✅ No console errors in frontend
- ✅ RBAC restricts features correctly
- ✅ Settings save and persist

---

**🚀 Ready for Production!**

**Support:** For issues, check logs in `logs/titan_system_log.txt` and BigQuery `system_error_log` table.

**Version:** 3.0.0-PRODUCTION  
**Build Date:** 2026-01-26  
**License:** Ever Built Proprietary
