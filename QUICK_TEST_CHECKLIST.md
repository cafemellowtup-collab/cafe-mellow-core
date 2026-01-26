# 🧪 QUICK TEST CHECKLIST - CEO MANUAL TESTING
**Time Required:** 15-20 minutes for complete validation

---

## ⚡ RAPID DEPLOYMENT VERIFICATION

### ✅ TEST 1: CREDENTIAL MANAGEMENT (2 min)
**Critical:** Prevents credential wipe bug

```
1. Open: http://localhost:3000/settings
2. Fill ALL fields:
   - PROJECT_ID: cafe-mellow-core-2026
   - DATASET_ID: cafe_operations
   - GEMINI_API_KEY: [paste key]
   - PP_APP_KEY: [paste key]
   - PP_APP_SECRET: [paste secret]
   - PP_ACCESS_TOKEN: [paste token]
   - PP_MAPPING_CODE: rest123
3. Click "Save"
4. Verify alert: "✅ Settings saved successfully!"
5. Only update PP_MAPPING_CODE to: rest456
6. Click "Save" again
7. ✅ PASS: All other fields still show "Set"
   ❌ FAIL: Any field shows "Missing"
```

---

### ✅ TEST 2: TITAN CFO PERSONALITY (3 min)
**Critical:** Verifies AI speaks like a CFO, not consultant

```
1. Open: http://localhost:3000/chat
2. Click: "Scan for Profit Leaks"
3. Wait for response (15-30 sec)
4. ✅ PASS if response has:
   - Starts with a NUMBER (e.g., "₹12,450 leaked")
   - Contains "Root cause:"
   - Contains "[TASK:]" or "Direct action:"
   - Uses short, directive sentences
5. ❌ FAIL if response says:
   - "You should consider..."
   - "It might be helpful to..."
   - Generic consultant-speak
```

**Example GOOD Response:**
```
Maida wastage: 12kg (₹840), up 23% vs last week. 
Root cause: Over-mixing in morning shift. 
[TASK:] Retrain prep staff on dough yield by tomorrow 10 AM.
```

---

### ✅ TEST 3: AUTO-TASKING (2 min)
**Critical:** Verifies tasks auto-create from AI directives

```
1. After chat response with [TASK:], run in BigQuery:
   
   SELECT * FROM ai_task_queue 
   WHERE status = 'Pending' 
   ORDER BY created_at DESC 
   LIMIT 1

2. ✅ PASS: New task appears with:
   - description = text after [TASK:]
   - task_type = "AI_Generated_Action"
   - status = "Pending"
   - deadline populated
3. ❌ FAIL: No task created
```

---

### ✅ TEST 4: UNIVERSAL INGESTER (5 min)
**Critical:** Verifies multi-modal data pipeline

```
1. Get service account email:
   GET http://localhost:8000/api/v1/ingester/service-account
   
2. Share a Google Drive folder with this email (Viewer)

3. Test connection:
   POST http://localhost:8000/api/v1/ingester/test-connection
   Body: {"folder_id": "YOUR_FOLDER_ID"}
   
4. ✅ PASS: Returns {"accessible": true, "sample_files": [...]}
   ❌ FAIL: Returns {"accessible": false}

5. Upload test file (expenses.xlsx) to folder

6. Run ingestion:
   POST http://localhost:8000/api/v1/ingester/ingest
   Body: {
     "folder_id": "YOUR_FOLDER_ID",
     "master_category": "expenses"
   }
   
7. Check status after 30 seconds:
   GET http://localhost:8000/api/v1/ingester/status/{job_id}
   
8. ✅ PASS: {"success": 1, "failed": 0}
   ❌ FAIL: {"success": 0, "failed": 1}
```

---

### ✅ TEST 5: DATABASE LOCKING (2 min)
**Critical:** Prevents race conditions

```
1. Open 2 terminals
2. Terminal 1: python 01_Data_Sync/sync_expenses.py
3. Terminal 2 (immediately): python 01_Data_Sync/sync_expenses.py
4. ✅ PASS: Terminal 2 shows "Skipped - another process syncing"
   ❌ FAIL: Both terminals sync simultaneously
```

---

### ✅ TEST 6: CHAT UI LAYOUT (1 min)
**Visual:** Verify enterprise-grade interface

```
1. Open: http://localhost:3000/chat
2. ✅ PASS if:
   - Sidebar = 20% width (left)
   - Chat area = 80% width (right)
   - "CEO Command Chips" visible above input
   - Live status shows during AI thinking
3. ❌ FAIL: Old layout (sidebar too wide or missing)
```

---

## 🚨 CRITICAL FAILURES - STOP DEPLOYMENT

If ANY of these fail, DO NOT proceed to production:

1. ❌ TEST 1 FAIL: Credentials getting wiped
2. ❌ TEST 3 FAIL: Tasks not auto-creating
3. ❌ TEST 4 FAIL: Ingester cannot access Drive
4. ❌ TEST 5 FAIL: Race conditions occurring

## ⚠️ WARNING FAILURES - Fix Before Production

If these fail, fix but can still test other features:

1. ⚠️ TEST 2 FAIL: AI personality wrong (tune prompt)
2. ⚠️ TEST 6 FAIL: UI layout issues (CSS problem)

---

## 📊 OPTIONAL: PERFORMANCE VALIDATION (5 min)

### Query Cost Check
```sql
SELECT 
  DATE(timestamp) as date,
  COUNT(*) as queries,
  SUM(cost_inr) as total_cost
FROM system_cost_log
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY date
ORDER BY date DESC
```
**✅ Target:** < ₹100/day average

### Chat Response Time
```
1. Ask: "Revenue last 7 days"
2. ✅ Target: Response within 10 seconds
```

### Ingestion Speed
```
1. Upload 500-row Excel file
2. ✅ Target: Processed in < 15 seconds
```

---

## 🎯 DEPLOYMENT GO/NO-GO DECISION

### ✅ GO FOR PRODUCTION IF:
- All 6 critical tests PASS
- No critical failures
- At most 1-2 warning failures

### ❌ NO-GO IF:
- Any critical test FAILS
- 3+ tests FAIL overall
- Race conditions detected
- Credentials getting wiped

---

## 🆘 QUICK FIXES

### "GEMINI_API_KEY missing after save"
```
- Use Settings UI (not direct API)
- Settings UI now uses PATCH automatically
- Previous bug FIXED in this deployment
```

### "Tasks not creating"
```
- Check AI response contains [TASK:]
- Run: SELECT COUNT(*) FROM ai_task_queue
- If table missing, sync scripts will create it
```

### "Ingester access denied"
```
- Verify exact email from /service-account endpoint
- Share folder with Viewer permission
- Wait 2 minutes for propagation
```

### "Chat timeout"
```
- Now 45 seconds (increased from 30)
- If still timing out, check BigQuery dataset size
- Limit chat_memory to 10 messages (already implemented)
```

---

## 📞 SUPPORT COMMANDS

### Check System Health
```bash
GET http://localhost:8000/health
```

### View Active Locks
```sql
SELECT * FROM system_locks 
WHERE expires_at > CURRENT_TIMESTAMP()
```

### View Recent Tasks
```sql
SELECT * FROM ai_task_queue 
WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
ORDER BY created_at DESC
```

### View Ingestion Log
```sql
SELECT * FROM folder_watcher_log 
ORDER BY run_timestamp DESC 
LIMIT 10
```

---

**Total Testing Time:** ~15 minutes  
**Automated Testing:** Coming soon (pytest suite)  
**Manual Testing Required:** Yes, for production validation  

**Status After Tests:** If all pass → ✅ DEPLOY TO PRODUCTION
