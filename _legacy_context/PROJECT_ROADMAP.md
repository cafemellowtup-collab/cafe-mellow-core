# 🗺️ TITAN ERP - Complete Project Roadmap & Cleanup Plan

**Version:** 6.5.0 - God Mode Complete  
**Last Updated:** February 1, 2026  
**Status:** Phase 6.5 Complete - Backend Finalized, Ready for UI  
**Goal:** Transform into infinitely expandable multi-industry platform

---

## 📋 EXECUTIVE SUMMARY

### **Project Vision**
Build an infinitely expandable AI-powered ERP platform that can serve ANY industry (restaurant, retail, healthcare, manufacturing, etc.) without touching existing code - just add new plugins/modules.

### **Current Reality**
- ✅ **Strong Foundation:** Modern tech stack (Next.js 16, React 19, FastAPI, BigQuery, Gemini AI)
- ✅ **Innovation:** Universal Semantic Brain that classifies ANY data automatically
- ⚠️ **Major Issues:** 35+ duplicate files, 3 competing AI engines, hardcoded restaurant logic
- 🎯 **Path Forward:** 6-week cleanup → multi-industry expansion

### **Key Decisions Needed**
1. **Choose ONE TITAN AI implementation** (Recommended: TITAN v3)
2. **Delete 35+ duplicate files** immediately
3. **Migrate to Universal Semantic Brain** fully
4. **Build industry plugin system**

---

## 🎉 PHASE 1 COMPLETE: REPAIR & RECONNECT (Jan 30, 2026)

### **Completed Tasks:**
- [x] **Server Stabilization** - Port conflict resolution, uvicorn startup fixes
- [x] **Backend Crash Fixes** - Unicode/Emoji encoding bugs (cp1252 → ASCII-safe logging)
- [x] **TITAN v3 Engine Connection** - Frontend Chat UI wired to TITAN v3 `process_query`
- [x] **Google Authentication (ADC)** - Application Default Credentials configured
- [x] **BigQuery Schema Fixes** - `SchemaField` `type=` → `field_type=` migration
- [x] **Gemini Model Updates** - Upgraded from deprecated 1.5 to 2.0-flash/2.5-pro
- [x] **Environment Loading** - Added `python-dotenv` for `.env` file support

### **Current Status:**
✅ TITAN v3 is **online, authenticated, and responding** in the Chat UI.

### **Observation:**
The AI responds but suffers from **"Data Tunnel Vision"** - it only sees 1-2 alerts and lacks robust business data context. The AI is functional but needs **real sales/inventory data** to provide actionable insights.

---

## 🎯 PHASE 2: DATA INGESTION & PIPELINE REPAIR (Current Focus)

### **Problem:**
TITAN v3 is intelligent but **data-starved**. Without consistent sales, inventory, and expense data flowing into BigQuery, the AI cannot provide meaningful business analysis.

### **Goals:**
1. **Fix PetPooja Sync** - Ensure daily sales data flows into `sales_raw`
2. **Inventory Pipeline** - Connect inventory tracking to `universal_events`
3. **Expense Ingestion** - Google Drive → BigQuery expense parsing
4. **Data Quality** - Validate data freshness and completeness
5. **AI Context Expansion** - Give TITAN access to 30+ days of business data

### **Completed Tasks:**
- [x] **Phase 2A: Configuration Centralization (The Lobotomy)** - Removed ALL hardcoded `cafe-mellow-core-2026` from Python files. Created `get_bq_config()` in `pillars/config_vault.py`. Refactored 16 files to use centralized config. *(Jan 30, 2026)*
- [x] **Phase 2B: Generic Tabular Ingestion Endpoint** - Built `/api/v1/ingest/file` endpoint accepting Excel/CSV files. Supports `.xlsx`, `.xls`, `.csv` formats via pandas + openpyxl. Multi-tenant via `X-Tenant-ID` header. **Verified: 5/5 tests passed.** *(Jan 30, 2026)*
- [x] **Phase 2C: Structure Detective (Header Hunter)** - Auto-detects header rows in messy files. Scans up to 500 rows. Uses "Golden Path" for instant detection on clean files. *(Jan 31, 2026)*
- [x] **Phase 2D: AI Safety Net (Gemini Judge)** - For ambiguous multi-table files, the AI Judge (Gemini Flash) disambiguates between competing header candidates. Prefers "Detail Ledgers" over "Summary Tables". *(Jan 31, 2026)*
- [x] **Phase 2E: Universal Mapper (Fuzzy Logic)** - Fuzzy column matching maps raw columns to semantic fields (timestamp, amount, entity, reference). Strips currency symbols (₹, $, Rs). Transforms rows into `UniversalEvent` objects. *(Jan 31, 2026)*

### **Phase 2 Achievements:**
- ✅ Any Excel/CSV file can be uploaded via `/api/v1/ingest/file`
- ✅ Headers auto-detected even in messy files (logos, titles, blank rows skipped)
- ✅ AI Judge resolves ambiguous multi-table scenarios
- ✅ Columns auto-mapped to semantic fields (date → timestamp, amount → value)
- ✅ Currency symbols stripped automatically (₹, $, Rs, commas)
- ✅ All rows transformed to strict `UniversalEvent` objects

---

## 🏰 PHASE 8: FORTRESS UPGRADE (IN PROGRESS - Feb 2, 2026)

### **Problem:**
Ingestion accepted junk/unknown files and lacked resilience for missing menu data.

### **Goals:**
1. **Bouncer:** Schema validation to reject junk/unknown files early
2. **Sherlock:** Deterministic STREAM (Sales) vs STATE (Menu) classification
3. **Turbo Engine:** Async batch classification in chunks of 50
4. **Ghost Logic:** Auto-create provisional items for unknown sales entities
5. **STATE Upserts:** Convert provisional items to official menu data

### **Progress:**
- [x] `semantic_brain.py` upgraded with Bouncer + Sherlock + Turbo
- [x] `ingest.py` pre-validates schema, rejects UNKNOWN with HTTP 400
- [x] `ledger_writer.py` handles Ghost Items + STATE upserts (local registry)
- [ ] Validate upload scenarios (Sales.csv, Random.csv)

---

## ✅ PHASE 3: THE UNIVERSAL LEDGER (COMPLETED - Jan 31, 2026)

### **Problem:**
Events are created but not yet persisted. We need to write them to BigQuery and enable AI classification.

### **Goals:**
1. **BigQuery Integration** - Write `UniversalEvent` objects to `universal_ledger` table
2. **AI Classification** - Auto-categorize events (Sales, Expenses, Inventory, etc.)
3. **Quarantine System** - Hold invalid/suspicious rows for human review
4. **Verification UI** - Allow humans to correct AI classifications
5. **Learning Loop** - AI improves from human corrections

### **Completed Tasks:**
- [x] **Phase 3A: Ledger Writer** - `LedgerWriter` class with dual-mode (BigQuery + Local fallback)
- [x] **Phase 3B: Semantic Brain** - `SemanticBrain.classify_batch()` with Gemini AI + cache
- [x] **Phase 3C: Quarantine Queue** - Traffic Cop routes low-confidence (<85%) to quarantine
- [x] **Phase 3D: Review API** - `/api/v1/quarantine/list` and `/resolve` endpoints

### **Key Files:**
- `backend/universal_adapter/ledger_writer.py` - Dual-mode storage engine
- `backend/universal_adapter/semantic_brain.py` - AI classifier with learning
- `api/routers/quarantine.py` - Review API endpoints
- `api/routers/ingest.py` - Ingestion pipeline (Detective → Mapper → Brain → Writer)

### **Success Criteria:**
- [x] Events persist to BigQuery `universal_ledger` table
- [x] AI classifies events with >85% confidence
- [x] Low-confidence events flagged for human review (quarantine_queue)
- [x] Human approval teaches Brain (cache updated)
- [ ] TITAN can answer: "What were my sales yesterday?" (Phase 4)
- [ ] TITAN can answer: "Which items are running low?" (Phase 4)

---

## ✅ PHASE 4: TITAN CORTEX & QUERY ENGINE (COMPLETED - Feb 1, 2026)

### **Problem:**
Data is now stored and classified, but users can't easily query it. We need natural language querying with adaptive AI personality.

### **Goals:**
1. **Natural Language Queries** - "What were my sales yesterday?" → SQL → Answer
2. **Smart Aggregations** - Auto-detect time ranges, groupings, filters
3. **Adaptive AI Personality** - Cortex adapts to user data maturity
4. **Simulation Mode** - Handle "What if?" questions without modifying data
5. **Deep History Analysis** - Understand user patterns over time

### **Completed Tasks:**
- [x] **Phase 4A: Titan Cortex** - Adaptive AI personality based on data maturity
- [x] **Phase 4B: Query Engine** - Natural language → BigQuery SQL → Human answer
- [x] **Phase 4C: Simulation Detection** - Handles "What if I sell 5kg?" questions
- [x] **Phase 4D: Deep History** - Analyzes data timeline for persona adaptation
- [x] **Phase 4E: Preference System** - User preferences (currency, fiscal year, exclusions)

### **Key Files:**
- `backend/universal_adapter/titan_cortex.py` - Adaptive AI personality engine
- `backend/universal_adapter/query_engine.py` - NL → SQL → Answer engine
- `api/routers/query.py` - Query API endpoints
- `data/user_preferences.json` - User preference storage

### **Success Criteria:**
- [x] User asks "What were my sales this week?" → Gets accurate answer
- [x] User asks "What if I sell 10kg at 500/kg?" → Gets simulation result
- [x] AI adapts persona based on data maturity (empty → full CFO)
- [x] Response time < 3 seconds for common queries

---

## ✅ PHASE 5: REFACTORING & SYSTEM EVOLUTION (COMPLETED - Feb 1, 2026)

### **Problem:**
`FutureWarning` from deprecated `google.generativeai` library. Need Creator Feedback Loop.

### **Goals:**
1. **Library Migration** - Move from `google.generativeai` to `google.genai`
2. **System Evolution** - Track user friction points, suggest features
3. **Code Cleanup** - Remove deprecated analytics and reports routers

### **Completed Tasks:**
- [x] **Phase 5A: Library Migration** - All files migrated to `google.genai`
- [x] **Phase 5B: System Evolution** - Friction logging and AI feature suggestions
- [x] **Phase 5C: Cleanup** - Deleted `analytics.py` and `reports.py`

### **Key Files:**
- `backend/core/system_evolution.py` - Friction tracking and feature suggestions
- `backend/universal_adapter/semantic_brain.py` - Migrated to google.genai
- `backend/universal_adapter/titan_cortex.py` - Migrated to google.genai
- `backend/universal_adapter/query_engine.py` - Migrated to google.genai

### **Success Criteria:**
- [x] No FutureWarning from google.generativeai
- [x] System Evolution logs friction points
- [x] AI suggests features based on friction patterns

---

## ✅ PHASE 6: MASTER COMMAND CENTER (COMPLETED - Feb 1, 2026)

### **Problem:**
Need "God Mode" for Master to control tenant features and AI behavior without touching core code.

### **Goals:**
1. **Feature Flags** - Enable/disable features per tenant
2. **Global Rules** - Inject AI behavior rules from Master
3. **The Link** - Cortex obeys Master's settings automatically

### **Completed Tasks:**
- [x] **Phase 6A: Master Config** - Tenant feature management and global rules
- [x] **Phase 6B: God Mode API** - Authenticated endpoints for Master control
- [x] **Phase 6C: The Link** - Cortex injects restrictions into AI prompts

### **Key Files:**
- `backend/core/master_config.py` - Central config manager
- `api/routers/master.py` - God Mode API endpoints
- `backend/universal_adapter/titan_cortex.py` - The Link integration

### **God Mode Endpoints:**
- `POST /api/v1/master/god/tenant/feature` - Enable/disable features
- `POST /api/v1/master/god/brain/rule` - Inject global AI rules
- `GET /api/v1/master/god/evolution/suggestions` - Get AI feature suggestions

### **Success Criteria:**
- [x] Master disables "simulation_mode" for Tenant X
- [x] Tenant X asks "What if?" → AI politely declines
- [x] Master adds rule "Be polite" → AI follows rule

---

## ✅ PHASE 6.5: FACTORY RESET & DOCUMENTATION (COMPLETED - Feb 1, 2026)

### **Problem:**
Need to clean test data and update documentation before UI phase.

### **Completed Tasks:**
- [x] **Factory Reset Tool** - `backend/tools/factory_reset.py`
- [x] **Documentation Sync** - Updated roadmap, vision, README

### **Key Files:**
- `backend/tools/factory_reset.py` - The Nuke Button
- `PROJECT_ROADMAP.md` - This file (updated)
- `VISION.md` - System manifesto
- `backend/README.md` - Backend documentation

---

## 🎯 PHASE 7: THE TITAN CONSOLE (Next Focus)

### **Problem:**
Backend is complete but needs a professional UI to showcase capabilities.

### **Goals:**
1. **Modern Dashboard** - Real-time metrics, charts, KPIs
2. **Chat Interface** - Polished TITAN conversation UI
3. **Data Upload** - Drag-and-drop file ingestion
4. **Quarantine Review** - Human review interface for low-confidence events
5. **Master Console** - God Mode control panel

### **Planned Tasks:**
- [ ] **Phase 7A: Dashboard Redesign** - Modern metrics cards and charts
- [ ] **Phase 7B: Chat Enhancement** - Streaming responses, code blocks, tables
- [ ] **Phase 7C: Upload Experience** - Drag-drop, progress, preview
- [ ] **Phase 7D: Quarantine UI** - Review, approve, reject interface
- [ ] **Phase 7E: Master Console** - Feature toggles, rules editor, evolution viewer

### **Success Criteria:**
- [ ] Dashboard loads < 2 seconds
- [ ] Chat feels responsive with streaming
- [ ] File upload shows real-time progress
- [ ] Master can control features via UI

---

## 🚨 CRITICAL ISSUES (MUST FIX FIRST)

### **ISSUE #1: Chat System Duplication**
**14 chat files** across backend/frontend with competing implementations.

**Backend (8 files):**
- ✅ KEEP: `utils/gemini_chat.py`, `utils/enhanced_chat.py`, `pillars/chat_intel.py`, `api/routers/chat.py`
- ❌ DELETE: `utils/gemini_chat_titan.py`, `utils/gemini_chat_backup.py`, `utils/gemini_chat_corrupted.py`, `utils/chat_interface.py`

**Frontend (6 files):**
- ✅ KEEP: `web/src/app/(dashboard)/chat/` (3 files)
- ❌ DELETE: `web/src/app/chat/` (entire folder - 3 files)

### **ISSUE #2: Three Competing TITAN AI Engines**
**THREE different implementations** with 80% overlap:

1. **TITAN v3** (`backend/core/titan_v3/`) - 6 modules, 100KB+
   - Self-learning, self-healing, external senses, knowledge graph
   - **RECOMMENDED TO KEEP**

2. **Intelligence Engine** (`backend/core/intelligence_engine.py`) - 26KB
   - Older, simpler, already integrated
   - **DELETE if keeping TITAN v3**

3. **Data Intelligence** (`backend/core/data_intelligence.py`) - 24KB
   - Oldest implementation
   - **DELETE if keeping TITAN v3**

**Decision:** Keep TITAN v3, delete the other two.

### **ISSUE #3: Duplicate Frontend Routes**
**5 duplicate route folders** outside Next.js route groups:
- ❌ DELETE: `web/src/app/chat/`, `web/src/app/dashboard/`, `web/src/app/operations/`, `web/src/app/settings/`, `web/src/app/master/`
- ✅ KEEP: `web/src/app/(dashboard)/`, `web/src/app/(master)/`, `web/src/app/(auth)/`, `web/src/app/(public)/`

### **ISSUE #4: Documentation Overload**
**30+ markdown files** with overlapping information.
- ✅ KEEP: `README.md`, `ARCHITECTURE.md`, `QUICKSTART.md`, `PROJECT_ROADMAP.md` (this file)
- 📦 ARCHIVE: 27 other docs to `docs/archive/`

### **ISSUE #5: Hardcoded Restaurant Logic**
Cannot expand to other industries without major refactoring:
- Hardcoded table names: `sales_raw`, `recipes_sales_master`, `wastage_log`
- Hardcoded UI labels: "Restaurant Dashboard", "Menu Items", "Recipe Management"
- POS-specific sync scripts

**Solution:** Migrate to Universal Semantic Brain (already built but not fully integrated).

---

## ✅ WHAT'S WORKING WELL

### **Strong Foundation**
1. ✅ Modern tech stack (Next.js 16, React 19, FastAPI, BigQuery, Gemini 2.0)
2. ✅ Multi-tenant architecture (proper tenant_id isolation)
3. ✅ **Universal Semantic Brain** - AI classification of ANY data (breakthrough!)
4. ✅ Immutable event ledger (complete audit trail)
5. ✅ JWT authentication + RBAC
6. ✅ Streaming chat (SSE)
7. ✅ Cost protection (BigQuery guardrails)

### **Universal Semantic Brain (Your Secret Weapon)**
- Classifies ANY data into 15+ categories automatically
- Confidence scoring (auto-store if >85%, human review if lower)
- Polymorphic storage (`universal_events` table)
- Can handle 2 Crore+ scenarios (20 million+)
- **This is EXACTLY what you need for multi-industry expansion!**

---

## 🧹 COMPLETE CLEANUP PLAN

### **Files to DELETE (35 files)**

#### **Backend (8 files)**
```
❌ utils/gemini_chat_titan.py
❌ utils/gemini_chat_backup.py
❌ utils/gemini_chat_corrupted.py
❌ utils/chat_interface.py
❌ backend/core/titan_prompts.py
❌ backend/core/intelligence_engine.py
❌ backend/core/data_intelligence.py
❌ api/routers/titan_core.py
```

#### **Frontend (5 folders ≈ 20 files)**
```
❌ web/src/app/chat/
❌ web/src/app/dashboard/
❌ web/src/app/operations/
❌ web/src/app/settings/
❌ web/src/app/master/
```

#### **Documentation (27 files → archive)**
```
📦 Move to docs/archive/:
- All deployment docs (11 files)
- All vision/mission docs (4 files)
- All status/summary docs (6 files)
- Architecture duplicates (3 files)
- Other misc docs (3 files)
```

### **Cleanup Steps**
```bash
# 1. Backup
git checkout -b backup-before-cleanup
git add -A && git commit -m "Backup before cleanup"

# 2. Delete duplicates
rm utils/gemini_chat_{titan,backup,corrupted}.py
rm -rf web/src/app/{chat,dashboard,operations,settings,master}
# ... (continue for all files)

# 3. Archive docs
mkdir docs/archive
mv DEPLOY*.md PRODUCTION*.md docs/archive/
# ... (continue for all 27 docs)

# 4. Test
uvicorn api.main:app --reload  # Backend
cd web && npm run dev          # Frontend

# 5. Commit
git checkout -b cleanup-duplicates
git add -A && git commit -m "Major cleanup: Remove 35 duplicates"
```

---

## 📅 6-WEEK ROADMAP

### **WEEK 1: Emergency Cleanup**
**Goal:** Remove duplicates, establish single source of truth

**Tasks:**
- [x] Delete 7 duplicate chat files
- [x] Choose TITAN implementation (keep v3, delete others)
- [ ] Delete 5 duplicate frontend route folders
- [ ] Archive 27 documentation files
- [ ] Test everything still works

**Deliverables:** 35 files deleted, all tests passing

---

### **WEEK 2: Architectural Clarity**
**Goal:** Establish clear layers and patterns

**Tasks:**
- [ ] Document layer responsibilities (Presentation → API → Business Logic → Data)
- [ ] Standardize data flow (no direct BigQuery in routers)
- [ ] Create coding standards document
- [ ] Audit codebase for violations
- [ ] Enforce patterns with linting rules

**Deliverables:** Clear architecture documented, all code follows standards

---

### **WEEK 3-4: Multi-Industry Foundation**
**Goal:** Migrate to Universal Semantic Brain, prepare for multi-industry

**Week 3 Tasks:**
- [ ] Audit all BigQuery queries
- [ ] Identify hardcoded table usage
- [ ] Update Universal Ingestion to handle all data types
- [ ] Test classification accuracy

**Week 4 Tasks:**
- [ ] Migrate dashboard queries to `universal_events`
- [ ] Migrate reports queries to `universal_events`
- [ ] Migrate chat queries to `universal_events`
- [ ] Update sync scripts
- [ ] Create industry plugin system architecture

**Deliverables:** 80%+ queries use Universal Semantic Brain, plugin system ready

---

### **WEEK 5-6: Production Hardening**
**Goal:** Fix remaining issues, comprehensive testing

**Tasks:**
- [ ] Create Google Cloud credentials setup guide (Windows)
- [ ] Add credential upload to Master dashboard
- [ ] Write comprehensive test suite (80%+ coverage)
- [ ] Performance optimization (API <500ms, frontend <3s)
- [ ] Security audit (OWASP ZAP, Bandit)
- [ ] Complete documentation (API reference, deployment guide)

**Deliverables:** Production-ready, fully tested, documented

---

## 🌍 MULTI-INDUSTRY EXPANSION (POST-CLEANUP)

### **Industry Plugin System Architecture**

```python
# backend/industries/base.py
class IndustryPlugin(ABC):
    @property
    def name(self) -> str:
        """Industry name"""
    
    @property
    def categories(self) -> List[str]:
        """Industry-specific categories"""
    
    def get_dashboard_config(self) -> Dict:
        """Dashboard metrics, charts"""
    
    def get_validation_rules(self) -> Dict:
        """Data validation rules"""
```

### **Restaurant Plugin (Current)**
```python
# backend/industries/restaurant.py
class RestaurantPlugin(IndustryPlugin):
    name = "Restaurant & Cafe"
    categories = ["menu_items", "recipes", "wastage", "reservations"]
    # ... dashboard config, validation rules
```

### **Retail Plugin (Future - Week 7-8)**
```python
# backend/industries/retail.py
class RetailPlugin(IndustryPlugin):
    name = "Retail & E-commerce"
    categories = ["products", "variants", "skus", "shipments", "returns"]
    # ... dashboard config, validation rules
```

### **Future Industries**
- **Q2 2026:** Healthcare, Professional Services
- **Q3 2026:** Manufacturing, Education
- **Q4 2026:** Real Estate, Automotive
- **2027:** Logistics, Hospitality, Fitness, Beauty

---

## 🎯 SUCCESS METRICS

### **Cleanup Phase (Weeks 1-2)**
- ✅ 35 files deleted
- ✅ 0 duplicate implementations
- ✅ 100% tests passing
- ✅ Clear architecture documented

### **Foundation Phase (Weeks 3-4)**
- ✅ 80%+ queries use Universal Semantic Brain
- ✅ Plugin system implemented
- ✅ UI is industry-agnostic

### **Production Phase (Weeks 5-6)**
- ✅ 80%+ test coverage
- ✅ API response <500ms (p95)
- ✅ Frontend load <3s
- ✅ Security audit passed

### **Multi-Industry Phase (Post-cleanup)**
- ✅ Can add new industry in 1 week
- ✅ No code changes to core system
- ✅ UI adapts automatically
- ✅ Data stays isolated by tenant

---

## 🚀 IMMEDIATE NEXT STEPS

### **Phase 3 Implementation (Next):**

1. **Create `backend/universal_adapter/ledger_writer.py`**
   - Batch insert `UniversalEvent` objects to BigQuery
   - Handle duplicates (idempotent writes)
   - Return success/failure counts

2. **Integrate AI Classification**
   - Call `SemanticBrain.classify()` before writing
   - Set `category`, `sub_category`, `confidence_score`

3. **Build Quarantine System**
   - Events with confidence <85% go to `quarantine_queue` table
   - API endpoint to list/review/approve quarantined items

4. **Connect to Dashboard**
   - TITAN queries `universal_ledger` for business insights
   - Dashboard charts pull from classified events

### **Cleanup Tasks (When Ready):**

1. Delete duplicate chat files (7 files)
2. Delete duplicate frontend routes (5 folders)
3. Archive old documentation (27 files)
4. Test everything still works

---

## 📚 KEY DOCUMENTS

After cleanup, you'll have only these docs:
- **README.md** - Main entry point, quick start
- **ARCHITECTURE.md** - Technical reference, system design
- **QUICKSTART.md** - Step-by-step setup guide
- **PROJECT_ROADMAP.md** - This file (complete roadmap)

All other docs archived to `docs/archive/` for reference.

---

## 💡 FINAL THOUGHTS

**Your app CAN be infinitely expandable, BUT you must:**

1. **First:** Clean up the mess (delete 35 duplicates)
2. **Second:** Establish clear architecture (one way to do things)
3. **Third:** Migrate to Universal Semantic Brain fully
4. **Fourth:** Build industry plugin system
5. **Fifth:** Make UI dynamic (no hardcoded labels)

**The Universal Semantic Brain you built is GENIUS** - it's exactly what you need for multi-industry expansion. You just need to **actually use it everywhere** instead of having old hardcoded logic alongside it.

**Timeline:**
- **With cleanup:** 4-6 weeks to multi-industry ready
- **Without cleanup:** 6-12 months (fighting technical debt)

**The choice is clear: Clean up first, then expand.**

---

**Ready to start?** Begin with Week 1 cleanup tasks. Delete those duplicate files and establish a single source of truth. Everything else will be easier after that.

**Questions?** Refer to this roadmap. Every decision, every task, every reason is documented here.

**Let's build something amazing! 🚀**
