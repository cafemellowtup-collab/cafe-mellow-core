# 🛡️ CAFE_AI PROJECT FLOW - DETAILED EXPLANATION

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Pattern](#architecture-pattern)
3. [Data Flow Pipeline](#data-flow-pipeline)
4. [Component Breakdown](#component-breakdown)
5. [Intelligence Layer](#intelligence-layer)
6. [User Interface](#user-interface)

---

## 🎯 System Overview

**CAFE_AI** (Project Titan) is an autonomous ERP system for Cafe Mellow that:
- Syncs data from multiple sources (Petpooja API, Google Drive)
- Parses and structures raw data into BigQuery
- Automatically detects financial anomalies, inventory gaps, and operational issues
- Provides a real-time dashboard for monitoring

**Core Philosophy**: Modular "Hub-and-Spoke" architecture where independent logic modules (Pillars) are dynamically loaded and executed.

---

## 🏗️ Architecture Pattern

### **Modular Pillar System**
```
Root (settings.py)
  ├── 01_Data_Sync/          → Data ingestion layer
  ├── 04_Intelligence_Lab/   → Sentinel analysis & monitoring
  │   ├── sentinel_hub.py    → The "Hub" (orchestrator)
  │   └── pillars/           → Sentinel Spokes (p1_revenue_integrity, p2_inventory_gap, p3_expense_purity)
  ├── pillars/               → App business logic (UI pillars)
  │   ├── evolution.py       → dev_evolution_log, Evolution Lab
  │   ├── dashboard.py       → Revenue/Expenses, Sentinel health, AI Observations
  │   ├── config_vault.py    → config_override.json, EffectiveSettings
  │   ├── users_roles.py     → titan_users.json, roles & tab access
  │   ├── chat_intel.py      → Logic-gap detection → dev_evolution_log
  │   └── system_logger.py   → logs/titan_system_log.txt + system_error_log (BQ)
  ├── titan_integrity.py     → DataIntegrityError, crash_report, append_crash_state (State of Data + exact line)
  ├── titan_app.py           → 5-tab Streamlit UI (Executive, Chat, User & Rights, API & Config, Evolution Lab)
  └── logs/titan_system_log.txt → Crash/error log (exact place + traceback + State of Data)
```

**Key Design Principles:**
1. **Separation of Concerns**: Data sync ≠ Intelligence ≠ UI
2. **Dynamic Loading**: Pillars are discovered and loaded at runtime
3. **Single Source of Truth**: `settings.py` contains all configuration
4. **TITAN-INTEGRITY**: Data Accuracy above all. Scripts crash rather than write incomplete data.

### **TITAN-INTEGRITY (Data Accuracy)**
- **No silent errors**: `try/except: pass` or `print(error)` replaced with `DataIntegrityError` and `crash_report`. BQ/API failures or missing required keys → raise and stop.
- **Pre-Validation**: Before any DELETE or WRITE_TRUNCATE, source must be validated. If source yields 0 rows when data was expected → `crash_report` and abort.
- **Slow-but-Sure**: `job.result(timeout=None)` for all BigQuery jobs. API `timeout=1800` (30 min). No timeouts that cause partial writes.
- **Crash reporting**: On integrity failure, `crash_report` writes to `logs/titan_system_log.txt` the **exact line**, **traceback**, and **State of Data** (e.g. `{date, rows_ready, api_status}`), then raises `DataIntegrityError`. `append_crash_state` used when catching `DataIntegrityError` at top level before `sys.exit(1)`.

---

## 🔄 Data Flow Pipeline

### **Phase 1: Data Ingestion (01_Data_Sync/)**

#### **1.1 Sales Data Sync** (`sync_sales_raw.py`)
```
Petpooja API → Raw JSON → BigQuery (sales_raw_layer)
```

**Process:**
- Fetches orders from Petpooja API for date range (default: last 90 days)
- Stores **complete JSON blob** in `sales_raw_layer` table
- Uses MD5 hash for deduplication
- Atomic replacement: Deletes day's data → Inserts fresh data

**Key Fields:**
- `order_id`: Unique order identifier
- `bill_date`: Date partition key
- `full_json`: Complete order JSON (preserved for later parsing)
- `row_hash`: MD5 hash for deduplication

#### **1.2 Sales Parsing** (`titan_sales_parser.py`)
```
sales_raw_layer (JSON) → Parse OrderItem array → sales_items_parsed (structured)
```

**Process:**
- Reads `full_json` from `sales_raw_layer`
- Extracts `OrderItem` array from JSON
- Creates structured rows: `item_name`, `quantity`, `unit_price`, `total_revenue`
- Writes to `sales_items_parsed` table (WRITE_TRUNCATE)

**Output Schema:**
```python
{
    "bill_date": DATE,
    "order_id": STRING,
    "item_name": STRING,
    "quantity": FLOAT,
    "unit_price": FLOAT,
    "total_revenue": FLOAT
}
```

#### **1.3 Expense Sync** (`sync_expenses.py`)
```
Google Drive Folder → Excel/CSV Files → expenses_master table
```

**Process:**
- Scans Google Drive folder (`FOLDER_ID_EXPENSES`)
- Reads Excel/CSV files with flexible header detection
- Extracts: Date, Amount, Category (Reason), Item Name (Explanation)
- Deduplicates using fingerprint: `date + amount + normalized_description`
- Writes to `expenses_master` table

**Key Logic:**
- **Ledger Format**: Expects `"Ledger Name - Category"` format
- **Deduplication**: Ignores category changes, focuses on date+amount+description

#### **1.4 Recipe Sync** (`sync_recipes.py`)
```
Google Drive Recipe Files → Parse Recipe Structure → recipes_sales_master table
```

**Process:**
- Scans Drive folder for files containing "Recipe"
- Parses Excel files with dynamic column detection
- Extracts: `parent_item` (menu item) → `ingredient_name`, `qty`, `unit`, `area`
- Handles multi-column recipe format (RawMaterial, Qty, Unit, Area blocks)

**Output Schema:**
```python
{
    "parent_item": STRING,      # Menu item (e.g., "Sandwich")
    "ingredient_name": STRING,   # Raw material (e.g., "Bread")
    "qty": FLOAT,
    "unit": STRING,
    "area": STRING,              # "All" or specific area
    "recipe_type": "SALES_LINK"
}
```

#### **1.5 Other Sync Scripts**
- `sync_cash.py`: Cash flow operations
- `sync_cash_ops.py`: Withdrawal/topup reports
- `sync_ingredients.py`: Ingredient master data
- `sync_production.py`: Production recipes (ingredient → raw material)
- `sync_purchases.py`: Purchase orders
- `sync_wastage.py`: Wastage logs

---

### **Phase 2: Intelligence Bridge**

#### **2.1 Name Bridge** (`titan_name_bridge` table)
```
Sales Item Names (Petpooja) ←→ Recipe Names (Your System)
```

**Problem Solved:**
- Petpooja item names ≠ Recipe file names (e.g., "Cappuccino" vs "Cappuccino Regular")
- Fuzzy matching bridges the gap

**How It Works:**
- `sales_items_parsed.item_name` → `titan_name_bridge.sales_name`
- `titan_name_bridge.recipe_name` → `recipes_sales_master.parent_item`

**Creation:**
- Manual mapping or fuzzy matching scripts (`evolution_v4_fuzzy_bridge.py`)
- Uses string similarity (RapidFuzz library)

---

### **Phase 3: Intelligence Layer (04_Intelligence_Lab/)**

#### **3.1 Sentinel Hub** (`sentinel_hub.py`) - The Orchestrator

**Flow:**
```
1. Import settings.py from root
2. Connect to BigQuery
3. Scan pillars/ folder for .py files
4. Dynamically load each pillar module
5. Call module.run_audit(client, settings)
6. Collect findings from all pillars
7. Upload to ai_task_queue table
```

**Key Features:**
- **Dynamic Discovery**: Automatically finds new pillar files
- **Fault Tolerance**: One pillar failure doesn't stop others
- **Standardized Interface**: All pillars must implement `run_audit(client, settings)`

#### **3.2 Pillar System** (`pillars/`)

**Pillar 1: Revenue Integrity** (`p1_revenue_integrity.py`)
- **Purpose**: Detect revenue leakage
- **Checks:**
  - Order cancellations (status = cancelled/void/deleted)
  - Discounts applied (extracts from Discount array)
- **Output**: Tasks for cancelled orders and discounts

**Pillar 2: Inventory Gap** (`p2_inventory_gap.py`)
- **Purpose**: Find unlinked sales items
- **Logic:**
  ```sql
  SELECT item_name FROM sales_items_parsed
  WHERE item_name NOT IN (SELECT sales_name FROM titan_name_bridge)
    AND item_name NOT IN (SELECT parent_item FROM recipes_sales_master)
  ```
- **Output**: Tasks for items without recipes

**Pillar 3: Expense Purity** (`p3_expense_purity.py`)
- **Purpose**: Tag personal/loan expenses
- **Logic:**
  - Scans `expenses_master` for items with " - " delimiter
  - Checks if category contains "personal", "loan", "interests"
  - Flags for AI to exclude from business P&L
- **Output**: Tasks for personal expense detection

**Pillar Interface:**
```python
def run_audit(client, settings):
    findings = []
    # ... audit logic ...
    return findings  # List of dicts with standardized schema
```

**Finding Schema:**
```python
{
    'created_at': datetime,
    'target_date': 'YYYY-MM-DD',
    'department': 'Finance' | 'Operations',
    'task_type': STRING,
    'item_involved': STRING,
    'description': STRING,
    'status': 'Pending',
    'priority': 'High' | 'Medium' | 'Low'
}
```

#### **3.3 Task Queue** (`ai_task_queue` table)
- **Purpose**: Centralized alert system
- **Storage**: All pillar findings → BigQuery table
- **Usage**: Dashboard reads from here to show alerts

---

### **Phase 4: User Interface** (`titan_app.py`)

**5-Tab Command Center (Glassmorphism, Dark Mode):**

1. **💎 Executive Dashboard**
   - AI Observations from `ai_task_queue`
   - Plotly: Revenue vs Expenses, Net
   - Sentinel Task Health

2. **🧠 Intelligence Chat**
   - Enhanced chat; on "I cannot answer" → `dev_evolution_log` (proposed)

3. **👥 User & Rights**
   - Roles: Admin, Manager, Staff; tab access; `titan_users.json`

4. **⚙️ API & Config Center**
   - PROJECT_ID, DATASET_ID, GEMINI_API_KEY, PP_* → `config_override.json` (no code edit)

5. **🧪 Evolution Lab**
   - Reads `dev_evolution_log`; Authorize to build (proposed → authorized)

**Sidebar:** TITAN_DNA.json, Update DNA, Run Sentinel, Role selector, `logs/titan_system_log.txt`

---

## 🔧 Configuration System (`settings.py`)

**Centralized Configuration:**
- Google Cloud credentials (`KEY_FILE`, `PROJECT_ID`)
- Database config (`DATASET_ID`, table names)
- Google Drive folder IDs
- API keys (Petpooja, Gemini)
- Magic strings (scope URLs, API endpoints)

**Path Resolution:**
- Root scripts: `import settings`
- Lab scripts: `sys.path.append(ROOT_DIR); import settings`
- Pillars: Receive `settings` object as parameter

---

## 📊 BigQuery Schema Overview

### **Core Tables:**

1. **`sales_raw_layer`**
   - Raw JSON dumps from Petpooja
   - Partitioned by `bill_date`

2. **`sales_items_parsed`**
   - Structured line items
   - One row per item per order

3. **`expenses_master`**
   - Cleaned expense records
   - Includes category tagging

4. **`recipes_sales_master`**
   - Menu item → Ingredient mappings
   - Includes area/zone information

5. **`titan_name_bridge`**
   - Sales name ↔ Recipe name mapping
   - Handles naming inconsistencies

6. **`ai_task_queue`**
   - Centralized alert system
   - All pillar findings stored here

7. **`dev_evolution_log`**
   - Self-development: user_query, logic_gap_detected, suggested_feature_specification, development_status
   - Fed by Intelligence Chat when it cannot answer; consumed by Evolution Lab

8. **`system_error_log`**
   - Runtime errors: module, file_path, line_number, error_message, traceback_text
   - Also written to `logs/titan_system_log.txt` for quick inspection

---

## 🔄 Complete Execution Flow

### **Daily Workflow:**

1. **Data Sync** (Run sync scripts)
   ```
   python 01_Data_Sync/sync_sales_raw.py
   python 01_Data_Sync/titan_sales_parser.py
   python 01_Data_Sync/sync_expenses.py
   python 01_Data_Sync/sync_recipes.py
   ```

2. **Intelligence Scan** (Run Sentinel Hub)
   ```
   python 04_Intelligence_Lab/sentinel_hub.py
   ```
   - Scans all pillars
   - Generates tasks
   - Uploads to `ai_task_queue`

3. **View Dashboard** (Streamlit UI)
   ```
   streamlit run titan_app.py
   ```
   - Shows financial metrics
   - Displays pending tasks
   - System DNA sidebar

---

## 🧬 System DNA (`titan_dna.py`)

**Purpose**: Living documentation; run after any structural change.

**Process:**
1. Scans `04_Intelligence_Lab/pillars/` (Sentinel) and root `pillars/` (App)
2. Scans root `.md` files; status `active` or `legacy`; lists `archived` under 99_Archive_Legacy
3. Writes `TITAN_DNA.json`: current_mission, sentinel_pillars, app_pillars, root_markdown, archived_markdown
4. Writes `SYSTEM_README.md` with **Current Mission** at top, then pillars and .md status

**Usage:**
```bash
python 04_Intelligence_Lab/titan_dna.py
```

**System Log:** Errors go to `logs/titan_system_log.txt` and `system_error_log` (BigQuery). Read the file to find exact error and place.

---

## 🎯 Key Design Patterns

### **1. Hub-and-Spoke**
- **Hub**: `sentinel_hub.py` (orchestrator)
- **Spokes**: Pillar files (independent logic)

### **2. Dynamic Module Loading**
- Uses `importlib.util` to load pillars at runtime
- No hardcoded imports

### **3. Configuration Injection**
- `settings` object passed to all pillars
- Single source of truth

### **4. Fault Tolerance**
- Try-except blocks in hub
- One pillar failure doesn't crash system

### **5. Atomic Operations**
- Data sync uses DELETE → INSERT pattern
- Prevents partial updates

---

## 🚀 Adding New Pillars

**Steps:**
1. Create new file in `pillars/` folder (e.g., `p4_new_audit.py`)
2. Implement `run_audit(client, settings)` function
3. Return list of findings (standardized schema)
4. Run `sentinel_hub.py` - it will automatically discover and execute

**Example:**
```python
from datetime import datetime

def run_audit(client, settings):
    findings = []
    # Your audit logic here
    findings.append({
        'created_at': datetime.now(),
        'target_date': '2026-01-20',
        'department': 'Finance',
        'task_type': 'Your Audit Type',
        'item_involved': 'Item Name',
        'description': 'Issue description',
        'status': 'Pending',
        'priority': 'High'
    })
    return findings
```

---

## 📝 Summary

**CAFE_AI** is a **modular, autonomous ERP system** that:
1. **Ingests** data from multiple sources (API + Drive)
2. **Structures** raw data into BigQuery tables
3. **Analyzes** data through independent pillar modules
4. **Alerts** via centralized task queue
5. **Visualizes** through Streamlit dashboard

**Key Strength**: The pillar system allows you to add new audit logic without modifying existing code - just drop a new file in `pillars/` and the hub will find and execute it.

---

*Last Updated: 2026-01-20*
*Version: 5.0.0 (5-tab Command Center, Evolution Lab, System Logger, DNA-driven docs)*
